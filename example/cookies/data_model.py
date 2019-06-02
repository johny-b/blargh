from blargh.data_model import DataModel
from blargh.data_model.fields import Scalar, Rel

#   Initialize the data model. This name 'cookies' is just an identifier,
#   useful if we are dealing with multiple data models.
dm = DataModel('cookies')

#   Create 'cookie' object. Each cookie has
#   *   id, which is an integer primary key
#   *   type, which is a string
cookie = dm.create_object('cookie')
cookie.add_field(Scalar('id', pkey=True, type_=int))
cookie.add_field(Scalar('type', type_=str))

#   Create 'jar' object. The only field is id, 
#   which is also an integer primary key
jar = dm.create_object('jar')
jar.add_field(Scalar('id', pkey=True, type_=int))

#   Add a relational field to cookie. 
#   This field ('jar') can hold at most one jar (and nothing else)
cookie.add_field(Rel('jar', stores=jar, multi=False))

#   Jar gets 'cookies' field, where any number of cookies can be held.
jar.add_field(Rel('cookies', stores=cookie, multi=True))

#   Until now, fields cookie.jar and jar.cookie could mean totally different things,
#   e.g. cookie.jar could be a jar with ingredients required to bake this cookie, 
#   and jar.cookies could be a list of all cookies that could fit in the jar.
#   
#   Now we declare that this is the same relationship: if certain cookie has certain
#   jar on its 'jar' field, this jar also has this cookie among its 'cookies'.
dm.connect(jar, 'cookies', cookie, 'jar')

#   dm object contains whole data model definition
__all__ = [dm]
