from ..exceptions import ProgrammingError

class Object():
    def __init__(self, name):
        self.name = name
        self._fields = []
        self._pkey_field = None
    
    def field(self, name, ext=False):
        for field in self._fields:
            if not ext and field.name == name:
                return field
            elif ext and field.ext_name == name:
                return field
    
    def fields(self):
        for field in self._fields:
            yield field
    
    def add_field(self, field):
        #   Check if field has correct names
        if self.field(field.name) is not None:
            raise ProgrammingError('field with name = \'{}\' already exists'.format(field.name))
        if self.field(field.ext_name, ext=True) is not None:
            raise ProgrammingError('field with ext_name = \'{}\' already exists'.format(field.ext_name))

        #   Add field
        self._fields.append(field)

        #   Set pkey
        if field.pkey():
            self._set_pkey(field)

    def _set_pkey(self, field):
        if self._pkey_field is not None:
            raise ProgrammingError('Pkey is already defined')
        self._pkey_field = field

    def __repr__(self):
        return str(self._fields)

    def pkey_field(self):
        return self._pkey_field
