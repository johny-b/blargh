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
        #   ID_ is either a string or a number, only way to
        #   guess which is really pkey is to parse it using object's pkey field
        obj = self.dm.object(name)
        pkey_field = obj.pkey_field()
        id_ = pkey_field.val(id_).stored()
    
        if id_ in self._current_instances[name]:
            instance = self._current_instances[name][id_]
        else:
            instance_data = self.storage.load(name, id_)
            instance = self._create_instance(name, instance_data)
        return instance
    
    @only_in_transaction
    def get_instances(self, name, filter_kwargs):
        '''Returns all instances which representation would be a superset of FILTER_KWARGS'''
        #   currently searching is allowed only by
        #   *   scalar fields
        #   *   single rel fields 
        #   
        #   filter_kwargs has external names and repr values, 
        #   dictionary internal_name -> stored_value is created 
        #   and than passed to Storage.selected_ids
        write_repr = {}
        model = self.dm.object(name)
        for key, val in filter_kwargs.items():
            field = model.field(key, ext=True)
            if field is None:
                raise exceptions.FieldDoesNotExist(object_name=name, field_name=key)
            elif field.rel:
                if field.multi:
                    raise exceptions.SearchForbidden(object_name=name, field_name=key)
                else:
                    #   REL field filter -> only IDs are alowed
                    write_repr[field.name] = field.stores.pkey_field().val(val).stored()
            elif field.stored:
                write_repr[field.name] = field.val(val).stored()
            else:
                raise exceptions.SearchForbidden(object_name=name, field_name=key)
            
        #   Fetch IDs
        ids = self.storage.selected_ids(name, write_repr)
        
        #   Return created instances
        return [self.get_instance(name, id_) for id_ in ids]
    
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

