from .object import Object
from ..exceptions import ProgrammingError

class DataModel():
    def __init__(self, name=None):
        self._objects = {}
        self._relationships = set()
        self.name = name
    
    def objects(self):
        return self._objects.copy()

    def object(self, name):
        return self._objects.get(name)

    def create_object(self, name):
        self.add_object(Object(name))
        return self.object(name)
    
    def add_object(self, obj):
        name = obj.name
        if self.object(name) is not None:
            raise ProgrammingError('{} already exists'.format(name))
        self._objects[name] = obj

    def connect(self, obj_1, fname_1, obj_2, fname_2):
        f1 = obj_1.field(fname_1)
        f2 = obj_2.field(fname_2)

        for field in (f1, f2):
            if field.other is not None:
                raise ProgrammingError('field {} is already connected'.format(field.name))

        for field, obj in ((f1, obj_2), (f2, obj_1)):
            if field.stores != obj:
                raise ProgrammingError('Field {} stores {} - could not be connect to field on {}'.
                                       format(field.name, field.stores.name, obj.name))

        if f1.multi and f2.multi:
            raise NotImplementedError("Connection between two multi fields is not implemented")
        
        if f1.default or f2.default:
            #   Connected fields would require update on existing objects during object creation,
            #   this could probably be done, but causes many additional complications (i.e. what if
            #   in one post we create more than one object, with the same default value of single relation?)
            raise NotImplementedError("Connection between fields with not-empty defaults is not implemented")

        f1.other = f2
        f2.other = f1

    def as_code(self):
        '''
        Returns list of lines, that joined and exec()uted should create the same DataModel.
        Used for testing and import.

        Used also in __eq__, because no better equality was implemented. This explains various 'sorted'.
        '''
        lines = []
        cls_set = set()
        cls_set.add(type(self))
        lines.append('')
        lines.append('dm = {}(\'{}\')'.format(type(self).__name__, self.name))
        lines.append('')

        #   rel fields should appear after all objects are created
        rel_lines = []

        for name, obj in sorted(self._objects.items()):
            lines.append('# {} object'.format(name))
            lines.append('{0} = dm.create_object(\'{0}\')'.format(name))
            for field in sorted(obj.fields(), key=lambda x: x.name):
                cls_set.add(type(field))
                field_lines = field.as_code()

                #   It is assumed that last line is SomeField(...), and lines before
                #   are additional things, (e.g. functions like setter)
                field_lines[-1] = '{}.add_field({})'.format(obj.name, field_lines[-1])

                #   A)  Rel field -> one line, stored now, added later
                #   B)  Scalar field -> one or more lines, added now
                #   C)  Calc field -> multiple lines, added now
                if field.rel:
                    rel_lines += field_lines
                else:
                    lines += field_lines

            lines.append('')
        
        lines.append("# rel fields")
        lines += rel_lines

        lines.append('')
        lines.append("# connections")
        already_connected = set()
        for obj_name, obj in sorted(self._objects.items()):
            for field in sorted(obj.fields(), key=lambda x: x.name):
                if field.rel and field.other and field not in already_connected:
                    other_field = field.other
                    lines.append('dm.connect({}, \'{}\', {}, \'{}\')'.
                                 format(field.stores.name, other_field.name, other_field.stores.name, field.name))

                    already_connected.add(field)
                    already_connected.add(other_field)
            
        import_lines = []
        for cls in sorted(cls_set, key=lambda x: x.__name__):
            import_lines.append('from {} import {}'.format(cls.__module__, cls.__name__))
        
        lines = import_lines + lines
        return lines

    def __eq__(self, other):
        return type(self) == type(other) and self.as_code() == other.as_code()
