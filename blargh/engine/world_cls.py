from .instance import Instance
from .. import exceptions

def only_in_transaction(f):
    def wrapped(world, *args, **kwargs):
        if not world._transaction_in_progress:
            raise exceptions.ProgrammingError('Method {} requires prior begin()'.format(f.__name__))
        return f(world, *args, **kwargs)
    return wrapped

class World():
    '''
    IS THIS A REAL WORLD?
    '''
    
    def __init__(self, dm, storage):
        self.dm = dm
        self.storage = storage
        
        self._current_instances = {}
        for name in self.dm.objects():
            self._current_instances[name] = {}

        self._auth = {}
        self._transaction_in_progress = False
    
    #   TRANSACTION MANAGMENT
    def begin(self):
        if self._any_instance():
            raise exceptions.ProgrammingError("Begin requires empty world")
        self._transaction_in_progress = True
        self.storage.begin()
    
    @only_in_transaction
    def commit(self):
        if self._any_instance():
            raise exceptions.ProgrammingError("Commit is allowed only with all changes written")
        self.storage.commit()
        self._transaction_in_progress = False

    @only_in_transaction
    def rollback(self):
        #   Remove all possible instances
        for instances in self._current_instances.values():
            instances.clear()
        self.storage.rollback()
        self._transaction_in_progress = False

    #   AUTHENTICATION
    def get_auth(self):
        return self._auth.copy()

    def set_auth(self, auth):
        #   This should never be possible, but indicated serious problem
        #   and we don't want to go unnoticed
        if self._auth:
            raise exceptions.ProgrammingError("auth currently set, use remove_auth() first")
        self._auth = auth

    def remove_auth(self):
        self._auth = {}
    
    #   DATA MODIFICATINS
    @only_in_transaction
    def new_instance(self, name, id_=None):
        '''Create new instance.'''
        if id_ is None:
            id_ = self.storage.next_id(name)

        pkey_field = self.dm.object(name).pkey_field()
        instance = self._create_instance(name, {pkey_field.name: id_})
        instance.changed_fields.add(pkey_field)

        return instance
    
    @only_in_transaction
    def get_instance(self, name, id_):
        '''Fetch instance from storage. Raises 404 if instance does not exist'''
        return self.get_instances_by_ids(name, [id_])[0]

    @only_in_transaction
    def get_instances_by_ids(self, name, ids):
        #   ID_ is either a string or a number, only way to
        #   guess which is really pkey is to parse it using object's pkey field.
        #   Possible dupliacates are also removed here.
        ids = [self.dm.object(name).pkey_field().val(id_).stored() for id_ in set(ids)]
        
        #   Find already created instances 
        instances = []
        new_ids = []
        for id_ in ids:
            if id_ in self._current_instances[name]:
                instances.append(self._current_instances[name][id_])
            else:
                new_ids.append(id_)

        if new_ids:
            instances_data = self.storage.load_many(name, new_ids)
            instances += [self._create_instance(name, d) for d in instances_data]
        return instances
    
    @only_in_transaction
    def get_instances(self, name, filter_kwargs, sort=None, limit=None):
        '''Returns all instances which representation would be a superset of FILTER_KWARGS,
        SORTed and LIMITed **only if current storage implements sort/limit**

        NOTE: filter_kwargs and sort both use external column names, straight from the client
        '''
        model = self.dm.object(name)
        write_repr = self._filter_kwargs_2_write_repr(model, filter_kwargs)
        sort = self._ext_stort_2_int_sort(model, sort)
            
        #   Fetch IDs
        ids = self.storage.selected_ids(name, write_repr, sort=sort, limit=limit)

        return self.get_instances_by_ids(name, ids)
    
    @only_in_transaction
    def write(self):
        '''
        Write all changes to the database. This does not commit any changes, but
        e.g. allows to call get_instance on freshly created instances.
        '''
        while True:
            instance = self._any_instance()
            if instance is None:
                break
            
            #   save instance, if changed
            if instance.changed():
                self.storage.save(instance)
        
            #   Foreget about this instance
            name = instance.model.name
            id_ = instance.id()
            del self._current_instances[name][id_]

            #   And make it no longer usable
            instance.usable = False
    
    @only_in_transaction
    def remove_instance(self, instance):
        '''
        Delete instance. Storage is modified, but changes are not commited yet.
        '''
        name = instance.model.name
        id_ = instance.id()
        
        #   Remove from storage and current instances
        self.storage.delete(name, id_)
        del self._current_instances[name][id_]
    
    #   OTHER METHODS
    def get_instance_class(self, name):
        '''Returns instance class for NAME objects. Currently always blargh.engine.Instance'''
        return Instance

    def data(self):
        '''Returns copy of all storage data. Debug/testing only.'''
        from copy import deepcopy
        return deepcopy(self.storage.data())
    
    def _create_instance(self, name, data):
        model = self.dm.object(name)
        instance = Instance(model, data)
        self._current_instances[model.name][instance.id()] = instance
        return instance
    
    def _any_instance(self):
        '''Returns any already created instance, or None if there are no current instances'''
        for instances in self._current_instances.values():
            if instances:
                return list(instances.values())[0]

    def _filter_kwargs_2_write_repr(self, model, filter_kwargs):
        '''
        currently searching is allowed only by
        *   scalar fields
        *   single rel fields 
        
        filter_kwargs has external names and repr values, 
        dictionary internal_name -> stored_value is returned
        '''
        write_repr = {}
        for key, val in filter_kwargs.items():
            field = model.field(key, ext=True)
            if field is None:
                raise exceptions.FieldDoesNotExist(object_name=model.name, field_name=key)
            elif field.rel:
                if field.multi:
                    raise exceptions.SearchForbidden(object_name=model.name, field_name=key)
                else:
                    #   REL field filter -> only IDs are alowed
                    write_repr[field.name] = field.stores.pkey_field().val(val).stored()
            elif field.stored:
                write_repr[field.name] = field.val(val).stored()
            else:
                raise exceptions.SearchForbidden(object_name=model.name, field_name=key)

        return write_repr

    def _ext_stort_2_int_sort(self, model, ext_sort):
        '''
        IN: [some_ext_name, -other_ext_name] etc
        OUT: #int_column_name   reversed
            [
             (some_int_name,    False),
             (other_int_name,   True),
            ]
        '''
        if not ext_sort:
            return []

        res = []
        for name in ext_sort:
            if name.startswith('-'):
                ext_name = name[1:]
                reversed_ = True
            else:
                ext_name = name
                reversed_ = False
            int_name = model.field(ext_name, ext=True).name
            res.append((int_name, reversed_))
        return res
