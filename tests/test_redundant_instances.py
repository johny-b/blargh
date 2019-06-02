'''
Test if instances are created only when really needed, so:
    *   when they are requested in any method (created, patched, etc)
    *   when other related instance is GETed with sufficient depth 

We check if World._create_instance is called excpected number of times.

'''


from example import family
from blargh.engine import world_cls

import importlib

import pytest

@pytest.fixture(autouse=True)
def cleanup():
    '''Reload world_cls after each test'''
    yield
    importlib.reload(world_cls)

@pytest.mark.parametrize("method, args, create_cnt", (
    ('get', ('child', 1), 1),
    ('get', ('child',), 3),
    ('get', ('child', None, {}, 2), 7),
    ('get', ('child', 1, None, 2), 3),
    ('get', ('child', 1, None, 3), 4),
    ('get', ('child', 1, None, 4), 5),
    ('get', ('child', 1, None, 4), 5),
    
    #   NOTE: patch/post/put creates instance(s), writes changes, and creates returned instance(s) again, 
    #   to return it GET-like, so cnts are one (or more, if POSTed multiple objects) bigger than one would expect
    ('patch', ('child', 1, {}), 2),
    ('patch', ('child', 1, {'father': None}), 3),
    ('patch', ('child', 2, {'father': 1}), 4),
    ('patch', ('male', 1, {'children': [1, 2, 3]}), 4),
    
    ('post', ('child', {'name': 'a'}), 2),
    ('post', ('child', [{'name': 'a'}, {'name': 'b'}]), 4),
    ('post', ('male', {'children': [1, {'name': 'a'}]}), 5),

    ('put', ('female', 3, {'children': [1, 2]}), 6),
    ('put', ('female', 3, {'husband': 1}), 4),
    
    ('delete', ('female', 1), 3),
    ('delete', ('female', 2), 4),
    ('delete', ('child', 1), 3),
))
def test_cnt(cleanup, init_world, get_client, method, args, create_cnt):
    init_world(family.dm)
    client = get_client()
    
    #   Modify world.get_instance to make it count it's calls
    cnts = {'create': 0}
    
    def wrap_create_instance(create_instance):
        def wrapped_create_instance(*args, **kwargs):
            print("\nCREATE INSTANCE!", *args[1:])
            cnts['create'] += 1
            return create_instance(*args, **kwargs)
        return wrapped_create_instance

    world_cls.World._create_instance = wrap_create_instance(world_cls.World._create_instance)
    
    data, status, headers = getattr(client, method)(*args)
    
    assert 200 <= status < 300
    assert cnts['create'] == create_cnt
