'''
Storage should implement commit/rollback.
Simple test to check if:
    *   world.data() didn't change when rolled back
    *   world.data() changed when commited
'''

from blargh.engine import world
from example import cookies

import pytest
from copy import deepcopy

@pytest.mark.parametrize("finalize, equal", (('rollback', True), ('commit', False)))
@pytest.mark.parametrize("operation", (
    lambda w: w.get_instance('cookie', 1).delete(), 
    lambda w: w.get_instance('cookie', 2).delete(), 
    lambda w: w.new_instance('jar'),
    lambda w: w.get_instance('cookie', 3).update({'type': 'donut'}),
    lambda w: w.get_instance('cookie', 3).update({'jar': {}}),
    lambda w: w.get_instance('cookie', 3).update({'jar': 1}),
))
def test_rollback_delete_1(init_world, finalize, equal, operation):
    init_world(cookies.dm)
    
    data_before = deepcopy(world().data())
    
    world().begin()
    operation(world())
    world().write()
    getattr(world(), finalize)()
    
    assert (data_before == world().data()) is equal
