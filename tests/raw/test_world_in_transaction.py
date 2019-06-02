'''
Ensure some functions can be called only when world is in transaction.
'''

from blargh.engine import world
from blargh import exceptions
from example import cookies
import pytest

@pytest.mark.parametrize("method, args", (
    ('new_instance', ('cookie',)),
    ('get_instance', ('cookie', 1)),
    ('get_instances', ('cookie', {})),
    ('write', ()),
))
def test_world_commit_1(init_world, method, args):
    '''Test most of the methods'''
    init_world(cookies.dm)
    w = world()
    
    #   Test 1
    with pytest.raises(exceptions.ProgrammingError):
        getattr(w, method)(*args)

    w.begin()
    
    #   Test 2 (not very intresting)
    getattr(w, method)(*args)
    
    w.write()
    w.commit()

    #   Test 3
    with pytest.raises(exceptions.ProgrammingError):
        getattr(w, method)(*args)

def test_world_commit_3(init_world):
    '''Test remove_instance()'''
    init_world(cookies.dm)
    w = world()
    w.begin()
    i = w.get_instance('cookie', 1)
    w.write()
    w.commit()
    with pytest.raises(exceptions.ProgrammingError):
        w.remove_instance(i)
