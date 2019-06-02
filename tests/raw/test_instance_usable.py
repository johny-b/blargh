'''
Written/deleted instances should be no longer usable.
This is a safeguard agains misusing Instance class.

Single world().write() writes all instances, so even 
those not changed should become unusable.
'''
from blargh.engine import world
from blargh import exceptions
from ..helpers.common import related
from example import family
import pytest

def test_usable_1(init_world):
    init_world(family.dm)
    world().begin()
    child = world().get_instance('child', 1)
    father = related(child, 'father')
    mother = related(child, 'mother')

    #   this one is not affected by change, but should still be unusable,
    #   because world writes all current instances
    other_child = world().get_instance('child', 2)

    child.delete()
    world().write()
    
    assert not child.usable
    assert not father.usable
    assert not mother.usable
    assert not other_child.usable

def test_usable_2(init_world):
    init_world(family.dm)
    world().begin()
    child = world().get_instance('child', 1)
    other_child = world().get_instance('child', 2)

    world().write()
    
    assert not child.usable
    assert not other_child.usable

def test_usable_3(init_world):
    init_world(family.dm)
    world().begin()
    child = world().new_instance('child')

    #   fresh instance is fine ...
    assert child.usable

    #   ... until written
    world().write()
    assert not child.usable


def test_usable_4(init_world):
    '''attempt to update not usable instance should raise an exception'''
    init_world(family.dm)
    
    world().begin()
    child = world().get_instance('child', 1)
    world().write()

    with pytest.raises(exceptions.ProgrammingError):
        child.update(dict(name='aaa'))

def test_usable_5(init_world):
    '''attempt to delete not usable instance should raise an exception'''
    init_world(family.dm)
    
    world().begin()
    child = world().get_instance('child', 1)
    world().write()

    with pytest.raises(Exception):
        child.delete()
