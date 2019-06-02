from blargh import exceptions
from blargh.engine import world

class SimpleValue():
    def __init__(self, val):
        self._val = val

    def repr(self, depth=1):
        return self._val

    def stored(self):
        return self._val

    def __eq__(self, other):
        return type(self) is type(other) and self._val == other._val

class ScalarValue(SimpleValue):
    def __init__(self, val, type_):
        if val is not None and type_ and type(val) != type_:
            #   We make an attepmt to cast val to type_, but only if
            #   *   simple cast works
            #   *   we are sure casting does not change the "real" meaning of data
            #       i.e. int('1') == 1 is fine, but
            #       i.e. int(1.1) == 1 is not, because 1.1 != 1
            #   The main purpose is to cast invisibly strings to integers, because
            #   there is no difference i.e. in urls ("api/cookie/7 - is it 7 or '7'?).
            #   
            #   Note that this might not work well for floats, because
            #   str(float('1')) == '1.0' so there is some change
            old_type = type(val)
            
            #   this might raise ValueError if casting does not work
            new_val = type_(val)

            #   and if casting works, but changes the data, we raise ValueError on our own
            if old_type(new_val) != val:
                raise ValueError

            val = new_val
        super().__init__(val)

class CalcValue(SimpleValue):
    def __init__(self, getter):
        self._getter = getter

    def repr(self, depth=1):
        return self._getter()

    def stored(self):
        return None

class RelValue(SimpleValue):
    def __init__(self, name, values):
        self.name = name
        
        if values is None:
            values = []
        elif type(values) is not list:
            if self.multi:
                raise exceptions.e400('invalid value')
            else:
                values = [values]
        elif type(values) is list and not self.multi:
            pass
            #   TODO
            # raise exceptions.e400('invalid value')

        self._ids = self._extract_ids(values)

    def _extract_ids(self, values):
        if not self.multi and len(values) > 1:
            raise exceptions.ProgrammingError('More than one instance on a Single related field')

        ids = []
        for val in values: 
            type_ = type(val)
            if val is None:
                raise exceptions.ProgrammingError("None is not accepted for {}".format(type(self)))
            elif type_ in (int, float, str):
                ids.append(val)
            elif issubclass(type_, world().get_instance_class(self.name)):
                ids.append(val.id())
            elif issubclass(type_, dict):
                inst = world().new_instance(self.name)
                inst.update(val)
                ids.append(inst.id())
            else:
                raise exceptions.ProgrammingError('could not create {}'.format(type(self)))
        return sorted(ids)
    
    def inst(self):
        return [world().get_instance(self.name, id_) for id_ in self._ids]
    
    def ids(self):
        return self._ids.copy()

    def __eq__(self, other):
        return type(self) is type(other) and \
                self.multi == other.multi and \
                self._ids == other._ids

class SingleRelValue(RelValue):
    multi = False
    def stored(self):
        return self._ids[0] if self._ids else None

    def repr(self, depth=1):
        if not self._ids:
            return None
        elif depth == 0:
            return self._ids[0]
        else:
            return self.inst()[0].repr(depth)
    
class MultiRelValue(RelValue):
    multi = True
    def stored(self):
        return self.ids()

    def repr(self, depth=1):
        if depth == 0:
            return self.ids()
        else:
            return [i.repr(depth) for i in self.inst()]

