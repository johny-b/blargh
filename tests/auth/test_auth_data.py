'''
Check auth - ensure world knows it's auth mehods work well.

There are two test methods:
    *   test_engine - check if "raw" engine works well
    *   test_clients - check if client calls work

Note: no storage-specific authentication is tested, we only test
      if world knows auth data.
'''

from example import cookies
from blargh.engine import Engine, world_cls
from blargh import exceptions
import importlib

import pytest

@pytest.fixture(autouse=True)
def cleanup():
    '''Reload world_cls after each test'''
    yield
    importlib.reload(world_cls)

def check_correct_auth(f, expected_auth):
    '''
    Wrapped function will check if current world auth
    matches expected auth
    '''
    def wrapped(*args, **kwargs):
        #   Check if we run on proper auth
        world = args[0]
        assert world.get_auth() == expected_auth

        #   Nothing else changes
        return f(*args, **kwargs)
    return wrapped

def check_no_auth(f):
    '''
    Wrapped function will check if current world auth
    matches expected auth
    '''
    def wrapped(*args, **kwargs):
        #   Check if we run on proper auth
        world = args[0]
        assert bool(world.get_auth()) is False

        #   Nothing else changes
        return f(*args, **kwargs)
    return wrapped

def add_world_wrappers(func, *args):
    w = world_cls.World
    w.new_instance = func(w.new_instance, *args)
    w.get_instance = func(w.get_instance, *args)
    w.get_instances = func(w.get_instances, *args)
    w.write = func(w.write, *args)

#   Tested calls
calls = (('get', 'cookie'), ('post', 'cookie', {}), ('put', 'cookie', 11, {}),
         ('patch', 'cookie', 1, {'jar': 2}), ('delete', 'cookie', 1),
         ('get', 'cookie', 77), ('post', 'cookie', {'foo': 'bar'}), ('delete', 'jar', 7))

#   Tested auth data
auth_data = (
    {'user_id': 7},
    {'f': 'oo', 'b': 'ar'},
    {},
    {'user': {'name': 'a', 'id': 11}},
)
@pytest.mark.parametrize("auth_data", auth_data)
def test_engine(init_world, auth_data):
    '''
    Test direct engine.Engine calls
    '''
    #   Initialization
    init_world(cookies.dm)

    #   TEST 1. CORRECT AUTH
    #   Add some wrappers
    add_world_wrappers(check_correct_auth, auth_data)

    for call in calls:
        method, *args = call
        try:
            getattr(Engine, method)(*args, auth=auth_data)
        except exceptions.ClientError:
            pass

    #   Cleanup
    importlib.reload(world_cls)

    #   TEST 2.  CHECK WITHOUT AUTH
    #   Add some wrappers
    add_world_wrappers(check_no_auth)

    #   Test
    for call in calls:
        method, *args = call
        try:
            getattr(Engine, method)(*args)
        except exceptions.ClientError:
            pass

@pytest.mark.parametrize("auth_data", auth_data)
def test_client(init_world, get_client, auth_data):
    '''
    test client calls
    '''
    #   Initialization
    init_world(cookies.dm)
    client = get_client(auth_required=True)
    client.login(auth_data)

    #   TEST 1. CORRECT AUTH
    #   Add some wrappers
    add_world_wrappers(check_correct_auth, auth_data)

    #   Test
    for call in calls:
        method, *args = call
        getattr(client, method)(*args)

    #   Cleanup
    importlib.reload(world_cls)

    #   TEST 2.  CHECK WITHOUT AUTH
    #   Add some wrappers
    client.logout()
    add_world_wrappers(check_no_auth)

    #   Test
    for call in calls:
        method, *args = call
        getattr(client, method)(*args)
