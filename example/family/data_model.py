from blargh.data_model import DataModel
from blargh.data_model.fields import Scalar, Rel, Calc

dm = DataModel('family')

#   OBJECTS & SCALAR FIELDS
male = dm.create_object('male')
male.add_field(Scalar('id', pkey=True, type_=int))
male.add_field(Scalar('name', type_=str))

female = dm.create_object('female')
female.add_field(Scalar('id', pkey=True, type_=int))
female.add_field(Scalar('name', type_=str))

child = dm.create_object('child')
child.add_field(Scalar('id', pkey=True, type_=int))
child.add_field(Scalar('name', type_=str))

#   REL FIELDS
male.add_field(Rel('wife',       stores=female, multi=False))    # noqa: E241
male.add_field(Rel('children',   stores=child,  multi=True))     # noqa: E241
female.add_field(Rel('husband',  stores=male,   multi=False))    # noqa: E241
female.add_field(Rel('children', stores=child,  multi=True))     # noqa: E241
child.add_field(Rel('father',    stores=male,   multi=False))    # noqa: E241
child.add_field(Rel('mother',    stores=female, multi=False))    # noqa: E241

#   CONNECTIONS
dm.connect(male,  'wife',   female, 'husband')      # noqa: E241
dm.connect(child, 'father', male,   'children')     # noqa: E241
dm.connect(child, 'mother', female, 'children')     # noqa: E241


#   CALC FIELDS
def url(instance):
    id_ = instance.id()
    if id_ is None:
        return None
    return "/".join([instance.model.name, str(id_)])


male.add_field(Calc('url', getter=url))
female.add_field(Calc('url', getter=url))
child.add_field(Calc('url', getter=url))
