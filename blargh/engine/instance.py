from blargh.engine import world
from .. import exceptions

class Instance():
    def __init__(self, model, data={}):
        '''Create instance with model MODEL.
        Initial values will be set from DATA. DATA should contain "storage" values.

        DATA might contain more values, i.e. database columns not represented in Instance datamodel,
        but they will not be accessible in any way.
        '''
        #   Instance has one defined data model,
        self.model = model

        #   and one value for each field defined by this model
        self._d = {}
        for field in self.model.fields():
            stored_value = data.get(field.name, field.default_stored(self))
            self._d[field] = field.val(stored_value)
        
        #   Instance has also few attributes tracking it's current state 
        #   in relation to current database state, history etc, such as
        #       changed_fields   -  set of fields that changed
        #       usable           -  boolean field, instance is usable until first (and only) write()/delete()
        #       deleted          -  boolean field, True if instance is deleted (more precisely, if delete started,
        #                           instance is still usable while being deleted)
        self.changed_fields = set()
        self.usable = True
        self.deleted = False
    
    #   PUBLIC INTERFACE
    def update(self, d):
        #   we are about to remove values, so copy is created
        d = d.copy()  

        #   Note: we iterate self.model.fields() (instead of d.items()) to ensure
        #   the same order of updated fields. This might make a difference with some Calc fields.
        for field in self.model.fields():
            ext_name = field.ext_name
            if ext_name not in d:
                continue

            repr_value = d.pop(ext_name)
            field.update(self, repr_value, True)
        
        #   Anything left - data contained incorrect field name
        if d:
            raise exceptions.FieldDoesNotExist(object_name=self.model.name, field_name=list(d)[0])
    
    def set_value(self, field, value):
        #   Not usable -> exception
        if not self.usable:
            raise exceptions.ProgrammingError("This instance is no longer usable")
        
        #   We don't bother with modyfying deleted instances
        #   (there is no way set_value influences anything else than this instance)
        if self.deleted:
            return
        
        #   Field not writable -> exception
        if not field.writable(self) or field.pkey():
            raise exceptions.FieldUpdateForbidden(object_name=self.model.name, field_name=field.ext_name)
        
        old_val = self.get_val(field)
        if old_val != value:
            #   Different value -> set it & note that field has changed
            self._d[field] = value
            self.changed_fields.add(field)

    def id(self):
        '''
        Returs instance's primary key value
        '''
        return self.get_val(self.model.pkey_field()).stored()

    def field_values(self):
        '''
        Yield all self's pairs (field, field_value).
        '''
        for field, val in self._d.items():
            yield field, val
    
    def get_val(self, field):
        '''Returns this instances FieldValue for given field'''
        return self._d[field]

    def get_val_by_name(self, field_name):
        '''Returns this instances FieldValue for given field name'''
        field = self.model.field(field_name)
        return self.get_val(field)

    def delete(self):
        '''
        Delete SELF:
            *   make other instances forget (by updating relationship fields)
            *   make world forget
        '''
        #   Not usable -> exception
        if not self.usable:
            raise exceptions.ProgrammingError("This instance is no longer usable")

        #   Delete started
        self.deleted = True
    
        for field, val in self.field_values():
            if field.rel and val is not None:
                field.propagate_delete(self)
        
        #   And the world will forget
        world().remove_instance(self)

        #   Instance should not be used any longer
        self.usable = False

    def repr(self, depth):
        '''
        Returns SELF (and related objects) as portable (i.e. json-serialisable) data structure.
        DEPTH (positive integer, default 0) defines how detailed the representation should be.
            0   ->  only ID
            >0  ->  all fields, objects on related field are presented with DEPTH - 1

        DEPTH is only limited by max python stack size, though it should be probably limited to 2 or 3.
        '''
        if depth < 0:
            raise exceptions.BadParamValue(param_name='depth', accepted_values='non-negative integer')
        
        if depth == 0:
            return self._0_repr()
        else:
            return self._1_repr(depth)
    
    def changed(self):
        return bool(self.changed_fields)

    #   PRIVATE METHODS
    def _0_repr(self):
        '''self.repr() for depth = 0'''
        return self.id()

    def _1_repr(self, depth):
        '''self.repr() for depth > 0'''
        d = {}
        for field, val in self.field_values():
            #   Hidden fields have no representation
            if field.hidden:
                continue
            
            #   Note: this 'depth - 1' is ignored if not field.rel, but
            #   could possibly be useful even for some custom fields
            repr_val = val.repr(depth - 1)

            #   Value is none -> key is not returned
            if repr_val is not None:
                d[field.ext_name] = repr_val

        return d

    def __repr__(self):
        return "{} ({})".format(self.model.name, self.id())
