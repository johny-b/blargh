from blargh import exceptions
from blargh.engine import world
from .values import ScalarValue, CalcValue, MultiRelValue, SingleRelValue

class Field():
    '''
    Base class of all fields, implements common attributes.

    Attributes:
        name: Internal (stored) field name
        ext_name: External field name, defaults to :code:`name`
        readonly: Boolean, if True user will not be allowed to set value of this field directly.
                  Readonly field can be changed either by other Calc field, or by updates to a connected
                  Rel field. Compare with :code:`writable`.
        default:  Default value of a field.
        _writable: Either boolean, or a function accepting :code:`blargh.engine.Instance` as only argument.
                  If evaluates to False, field can't be changed in any way - compare with :code:`readonly`.
                  Public interface: :code:`Field.writable(instance)`.
        hidden:   Boolean, if True field is not visible (so also can't be accessed directly), but still stored. 
                  Hidden field can be changed either by other Calc field, or by updates to a connected Rel field.
    
    '''
    def __init__(self, name, ext_name=None, readonly=False, default=None, writable=True, hidden=False):
        self.name = name
        self.ext_name = ext_name if ext_name is not None else name
        self.readonly = readonly
        self.hidden = hidden
        self.default = default
        self._writable = writable

    def writable(self, instance):
        if callable(self._writable):
            return self._writable(instance)
        return self._writable


    def load(self, instance, stored_value):
        instance.set_value(self, self.val(stored_value))

    def update(self, instance, repr_value, ext=False):
        if ext:
            if self.hidden:
                raise exceptions.FieldDoesNotExist(object_name=instance.model.name, field_name=self.ext_name)
            if self.readonly:
                raise exceptions.FieldIsReadonly(object_name=instance.model.name, field_name=self.ext_name)
        self._int_update(instance, repr_value, ext)

    def _int_update(self, instance, value, ext):
        instance.set_value(self, self.val(value))

    def default_stored(self, instance):
        return self.default

    def pkey(self):
        return False

    def stored(self):
        return True

    def as_code(self):
        lines = []
        if callable(self._writable):
            lines += _function_def(self._writable)
            writable = self._writable.__name__
        else:
            writable = self._writable
        
        lines.append('''{}('{}', ext_name='{}', writable={}, readonly={}, hidden={}, default={})'''.format(
                type(self).__name__, self.name, self.ext_name, writable, self.readonly, self.hidden, self.default))
        
        return lines

class Scalar(Field):
    '''
    Field storing a single value.
    This value can be complex (e.g. list or json), but is not parsed in any way - stored
    value is always the same as visible value.

    Beside attributes inherited from :code:`Field`, there are also:

    Attributes:
        pkey: If True, this field will be used in :code:`blargh.engine.Instance.id()`.
              Every object must have exactly one pkey field. Pkey fields are always readonly.
        type_: If anything else than None, values of this type will be accepted for this field.
              Values that can be reversibly casted to :code:`type_` are also accepted. E.g. :code:`'1'` 
              is accepted for :code:`int` field, because :code:`str(int('1')) == '1'`, 
              but :code:`'1 '` is not.
    '''
    rel = False

    def __init__(self, *args, pkey=False, type_=None, **kwargs):
        if pkey:
            if 'readonly' in kwargs and not kwargs['readonly']:
                raise exceptions.ProgrammingError("attempt to create non-readonly primary key field")
            if type_ is None:
                raise exceptions.ProgrammingError("PKey field requires type")
            kwargs['readonly'] = True
        super().__init__(*args, **kwargs)
        self._pkey = pkey
        self._type = type_

    def pkey(self):
        return self._pkey
    
    def type(self):
        return self._type

    def val(self, raw_value):
        try:
            return ScalarValue(raw_value, self._type)
        except (ValueError, TypeError):
            raise exceptions.BadFieldValue("Value does not match field's type", 
                                           value=raw_value, type=self._type.__name__, field_name=self.ext_name)

    def as_code(self):
        code = super().as_code()

        #   pkey and type_ is added to the last line
        type_name = None if self._type is None else self._type.__name__
        code[-1] = code[-1].replace(')', ', pkey={}, type_={})'.format(self._pkey, type_name))
        return code

class Calc(Field):
    '''
    Field that is not stored, but:

    *   when requested, it's value is computed (e.g. based on other fields)
    *   when updated, new value is passed to a function that updates other fields

    Main purpose is to allow interface that is independent from storage. For example,
    we might want to store kilometers, but allow end users to read/write miles.

    Attributes:
        getter: function accepting :code:`blargh.engine.Instance` as first and only argument, 
                and returning some value, e.g.

                .. code-block:: python
                    
                    def is_empty(jar):
                        cookies_field = jar.model.field('cookies')
                        cookies = jar.get_val(cookies_field).repr(0)
                        return not len(cookies)
                
                Default getter returns None.

        setter: function accepting :code:`blargh.engine.Instance` as first argument and anything as second,
                should return dictionary :code:`{'other_field_name': new_value_of_field}`, e.g:

                .. code-block:: python
                    
                    def ingredients(cookie, ingredients):
                        if 'milk' in ingredients:
                            new_type = 'muffin'
                        else:
                            new_type = 'shortbread'
                        return {'type': new_type}

                Default setter raises an exception.
                        
    '''
    
    rel = False
    
    @staticmethod
    def _default_getter(instance):
        return None
    
    @staticmethod
    def _default_setter(instance, value):
        raise exceptions.ProgrammingError("attempt to set value to Calc field without defined setter")

    def __init__(self, *args, getter=None, setter=None, **kwargs):
        if kwargs.get('hidden'):
            raise exceptions.ProgrammingError("Calc fields with hidden=True are not allowed")
        super().__init__(*args, **kwargs)
        self._getter = getter if getter else self._default_getter
        self._setter = setter if setter else self._default_setter
    
    def load(self, instance, value):
        if value is not None:
            #   just to be sure
            raise exceptions.ProgrammingError("Calc field 'value' should always be None")

        instance.set_value(self, self.val(lambda: self._getter(instance)))
    
    def _int_update(self, instance, value, ext):
        field_val_map = self._setter(instance, value)
        for ext_name, repr_value in field_val_map.items():
            field = instance.model.field(ext_name, ext=True)
            field.update(instance, repr_value)
    
    def default_stored(self, instance):
        return lambda: self._getter(instance)

    def stored(self):
        return False

    def val(self, raw_value):
        return CalcValue(raw_value)

    def as_code(self):
        code = super().as_code()
        
        lines, last_line = code[:-1], code[-1]

        if self._getter != self._default_getter:
            lines += _function_def(self._getter)
            getter = self._getter.__name__
        else:
            getter = None
        
        if self._setter != self._default_setter:
            lines += _function_def(self._setter)
            setter = self._setter.__name__
        else:
            setter = None
        

        last_line = last_line.replace(')', ', getter={}, setter={})'.format(getter, setter))
        lines.append(last_line)
        return lines


class Rel(Field):
    '''
    Field representing other objects.

    Relation could be one-way (e.g. jar knows it's cookies, but cookie has no idea if it is in a jar), 
    or two-way. Two-way relations are created with DataModel.connect().

    Attributes:
        stores: Defined type of objects on the other side of the relation 
                (heterogeneous relations are not allowed).
                Value should be :code:`engine.data_model.object.Object` (the thing returned by 
                :code:`DataModel.create_object('some_name')`). 
        multi: if True, any number of related objects is allowed, False - 0 or 1.
        cascade: if True, when this instance is deleted all related instances are also deleted.

    It is forbidden to set both :code:`multi=True` and :code:`cascade=True`.
    '''
    rel = True
    def __init__(self, *args, stores, multi, cascade=False, **kwargs):
        if multi:
            self._val_cls = MultiRelValue
            if 'default' in kwargs and type(kwargs['default']) is not list:
                raise exceptions.ProgrammingError("Multi field default must be a list")
            elif 'default' not in kwargs:
                kwargs['default'] = []
        else:
            self._val_cls = SingleRelValue
            if 'default' in kwargs and type(kwargs['default']) is list:
                raise exceptions.ProgrammingError("Multi field default cant be a list")
        
        super().__init__(*args, **kwargs)
        self.stores = stores
        self.multi = multi
        self.cascade = cascade

        if cascade and multi:
            #   multi + cascade is not implemented
            #   (i'm not sure how it should work)
            raise NotImplementedError("Cascade=True is not supported for Multi fields")
    

        #   this might be set in DataModel.connect(), but might also be left None
        self.other = None

    def val(self, raw_value):
        return self._val_cls(self.stores.name, raw_value)

    def _int_update(self, this_instance, value, ext):
        old_val = this_instance.get_val(self)
        new_val = self.val(value)
        
        if ext:
            #   If ext is True, we need to validate if new value objects really exist,
            #   the most straightforward way is to create instances stored in new_val.
            #   This would work well, but slow - we might end up creating many redundant instances.
            #   Instead here we extract new ids and validate only those.
            new_ids = set(new_val.ids()) - set(old_val.ids())
            new_ids_val = self.val(list(new_ids))
            new_ids_val.inst()
        
        this_instance.set_value(self, new_val)
        
        other = self.other
        if other:
            this_id = this_instance.id()
            added = set(new_val.ids()) - set(old_val.ids())
            removed = set(old_val.ids()) - set(new_val.ids())

            for added_id in added:
                other_instance = world().get_instance(self.stores.name, added_id)
                other_instance_ids = other_instance.get_val(other).ids()
                if this_id not in other_instance_ids:
                    if other.multi:
                        new_ids = sorted(other_instance_ids + [this_id])
                    else:
                        new_ids = [this_id]
                        if other_instance_ids:
                            disconnected_instance = world().get_instance(other.stores.name, other_instance_ids[0])
                            disconnected_instance.set_value(self, self.val(self.default))
                    other_instance.set_value(other, other.val(new_ids))
            
            for removed_id in removed:
                other_instance = world().get_instance(self.stores.name, removed_id)
                other_instance_ids = other_instance.get_val(other).ids()
                if this_id in other_instance_ids:
                    new_ids = other_instance_ids
                    new_ids.remove(this_id)
                    other_instance.set_value(other, other.val(new_ids))
    
    def propagate_delete(self, deleted_instance):
        '''
        DELETED_INSTANCE is being deleted.
        If SELF.other is not None, we need to remove all connections.
        '''
        other = self.other
        if other is None:
            return
        
        ids = deleted_instance.get_val(self).ids()

        for id_ in ids:
            this_id = deleted_instance.id()

            #   Other instance could have already been deleted, if we have multiple
            #   cascade fields - we just ignore it here
            try:
                other_instance = world().get_instance(self.stores.name, id_)
            except exceptions.e404:
                continue
            other_instance_ids = other_instance.get_val(other).ids()
            if this_id in other_instance_ids:
                #   If other.cascade, instance should also be deleted,
                #   if not - connection should be removed
                #   
                #   Note: if other.cascade is True, other.multi must be False (-> check Rel.init())
                #   so this is the only connection.
                #
                #   We also check instance.deleted to avoid recursion on recursive cascades
                if other.cascade and not other_instance.deleted:
                    other_instance.delete()
                else:
                    new_ids = other_instance_ids
                    new_ids.remove(this_id)
                    other_instance.set_value(other, other.val(new_ids))

    def as_code(self):
        code = super().as_code()

        #   stores, multi and cascade are added to args
        code[-1] = code[-1].replace(')', ', stores={}, multi={}, cascade={})'.format(
            self.stores.name, self.multi, self.cascade))
        return code

def _function_def(f):
    '''
    Returns lines of code for given function.
    Used internaly in AnyField.as_code().
    '''
    import inspect
    return inspect.getsource(f).split("\n")
