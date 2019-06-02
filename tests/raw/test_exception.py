'''
Test if we get expected exception.

Most of the exceptions are tested here, except:
    *   TransactionConflictRetriable, because it is (not directly) tested in 
        tests/pg_storage/test_serializable.py
    *   e400 - because it is raised only as generic Postgres error and tested in 
        tests/pg_storage/test_not_null.py
    *   e401/e422 because they are never raised (maybe they simply should be removed?)
    *   ClientError etc - because more specific exceptions are raised and tested

'''

from blargh import exceptions
from blargh.engine import Engine, dm
from blargh.data_model.fields import Scalar
from example import cookies
import pytest

class ExceptionRaiser:
    '''Each method raises exception of the same name'''
    def BadParamValue():
        Engine.get('cookie', 1, depth=-1)

    def SearchForbidden():
        Engine.get('jar', filter_={'cookies': [1, 2]})
    
    def FieldIsReadonly():
        #   Modify data model - cookie.type is readonly
        dm().object('cookie').field('type').readonly = True
        
        #   ... and yet we still try to change it!
        Engine.patch('cookie', 1, {'type': 'donut'})

    def FieldUpdateForbidden():
        #   Modify data model - we close our jars ...
        dm().object('jar').field('cookies')._writable = False

        #   ... and than try to remove the cookie from the jar
        Engine.patch('cookie', 1, {'jar': None})

    def FieldDoesNotExist():
        Engine.post('cookie', {'bad_field_name': 7})

    def e404():
        Engine.patch('cookie', 1, {'jar': 7})

    def ProgrammingError():
        #   field 'type' already exists
        dm().object('cookie').add_field(Scalar('type'))

    def e500():
        #   Note: maybe 4** would be more appropriate for bad 'auth' value, but
        #   we assume there is an intermediate layer between Engine and "user with auth",
        #   so bad auth on this level looks like a 500
        Engine.get('jar', 1, auth='aaa')

params = [[getattr(exceptions, name), getattr(ExceptionRaiser, name)] 
          for name in ExceptionRaiser.__dict__ if not name.startswith('__')]

@pytest.mark.parametrize('exception, method', params)
def test_exceptions(init_world, exception, method):
    init_world(cookies.dm)
    with pytest.raises(exception):
        method()

