'''
Test "raw" delete.

Note: world.begin() is required for PGStorage.
      world.commit() is never needed.
'''

from blargh.engine import world
from example import family, cookies
from ..helpers.common import related

def test_delete_1(init_world):
    init_world(family.dm)
    child_id = 1
    world().begin()
    child = world().get_instance('child', child_id)
    father = related(child, 'father')
    mother = related(child, 'mother')

    child.delete()

    assert child not in related(father, 'children')
    assert child not in related(mother, 'children')
    assert child_id not in world().data()['child']

def test_delete_2(init_world):
    init_world(family.dm)
    male_id = 1
    world().begin()
    male = world().get_instance('male', male_id)
    wife = related(male, 'wife')
    children = related(male, 'children')
    
    male.delete()

    assert related(wife, 'husband') is None
    for child in children:
        assert related(child, 'father') is None
    assert male_id not in world().data()['male']

def test_delete_3(init_world):
    init_world(cookies.dm)

    cookie_id = 2
    world().begin()
    cookie = world().get_instance('cookie', cookie_id)
    jar = related(cookie, 'jar')
    
    cookie.delete()

    assert cookie not in related(jar, 'cookies')
    assert cookie_id not in world().data()['cookie']

def test_delete_4(init_world):
    init_world(cookies.dm)

    jar_id = 1
    world().begin()
    jar = world().get_instance('jar', jar_id)
    jar_1_cookies = related(jar, 'cookies')

    jar.delete()
    
    for cookie in jar_1_cookies:
        assert related(cookie, 'jar') is None
    assert jar_id not in world().data()['jar']
