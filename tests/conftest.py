'''
DIRECTORY STRUCTURE
    tests/conftest.py   -   this file, used by pytest
    tests/helpers       -   many "helper" functions, to keep test code cleaner, no test functions
    tests/create        -   all creation methods from example/* should yield the same results
    tests/raw           -   tests explicitly calling world, instance etc. There are only few such tests,
                            because there are only few things that are hard to test from "api" functions
    test/*              -   all other testing functions

TEST PARAMETRIZATION
Most test are parametrized in three ways:
    *   init_world - there few possible worlds, and unless there is a known reason, 
        everything should work the same way for every world
    *   get_client - just like init_world, there is more than one client
    *   function-specific params

init_world and get_client are parametrized below, in pytest_generate_tests,
all other params are just before function declarations.


'''


import sys
sys.path.append('.')

print(sys.path)

from .helpers.blargh_config import init_world_functions, test_clients

def pytest_generate_tests(metafunc):
    #   Each test function somehow creates world().
    #   It might either
    #       *   has own defined creation method
    #       *   has init_world fixture
    #   In the second case, it will be run once for each function in helpers.blargh_config.init_world_function.
    if 'init_world' in metafunc.fixturenames:
        metafunc.parametrize('init_world', init_world_functions)

    #   This is simmilar to init_world. There are few test clients, each function tested on all of them
    #   has 'get_client' fixture parametrized here.
    if 'get_client' in metafunc.fixturenames:
        metafunc.parametrize('get_client', test_clients)
