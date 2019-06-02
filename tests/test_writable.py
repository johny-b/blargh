'''
Test field 'writable' attribute.

We test few separate things:
    *   We change cookie 'type' field - from now on it might be changed only when 
        cookie is not in jar.
    *   We change cookie 'jar' field - cookie once put in a jar may never
        be removed, only eaten (deleted, in other words, but still inside jar : ))
    *   We set 'wife' field of male to never-writable
    *   We set 'children' field of male to never-writable
'''

from blargh.engine import dm
from example import cookies, family

import pytest

def set_writable_1():
    '''
    TEST 1 - type changes only when not in the jar
    '''
    def not_in_jar(instance):
        return instance.get_val(instance.model.field('jar')).repr() is None

    cookie_obj = dm().object('cookie')
    cookie_obj.field('type')._writable = not_in_jar

def set_writable_2():
    '''
    TEST 2 - no removing from the jar
    '''
    def not_in_jar(instance):
        return instance.get_val(instance.model.field('jar')).repr() is None

    cookie_obj = dm().object('cookie')
    cookie_obj.field('jar')._writable = not_in_jar

params = (
    #   "Fresh" cookie is not in a jar, co it's always writable
    (1, 201, 'post', ('cookie', {'type': 'donut'})),
    (1, 201, 'post', ('cookie', {'type': 'donut', 'jar': 1})),
    (1, 201, 'put', ('cookie', 4, {'type': 'donut'})),
    (1, 201, 'put', ('cookie', 1, {'type': 'donut'})),
    (1, 201, 'put', ('cookie', 4, {'type': 'donut', 'jar': 1})),
    (1, 201, 'put', ('cookie', 4, {'jar': 1, 'type': 'donut'})),

    #   But cookie already in a jar is not
    (1, 400, 'patch', ('cookie', 1, {'type': 'donut'})),
    (1, 400, 'patch', ('cookie', 2, {'type': 'donut'})),
    (1, 400, 'patch', ('cookie', 3, {'type': 'donut'})),
    
    #   Note: from the "cookie" point of view, those two calls are the same (cookie stays in it's jar),
    #   but they have different results. This is intended - only explicit updates are really forbidden,
    #   such as the first case, but implicit updates take place only when something really changes.
    (2, 400, 'patch', ('cookie', 3, {'jar': 2})),
    (2, 200, 'patch', ('jar', 2, {'cookies': [3]})),
    
    #   Here we have two times 400 - both requests modify third cookie's jar
    (2, 400, 'patch', ('cookie', 3, {'jar': 1})),
    (2, 400, 'patch', ('jar', 1, {'cookies': [1, 2, 3]})),

    #   Some more implicit cookie.jar modifications
    (2, 400, 'patch', ('jar', 1, {'cookies': [1, 2, 3]})),
    (2, 400, 'patch', ('jar', 2, {'cookies': [1, 2, 3]})),
    (2, 400, 'patch', ('jar', 1, {'cookies': [1]})),
    (2, 400, 'patch', ('jar', 2, {'cookies': [1]})),
    (2, 400, 'patch', ('jar', 1, {'cookies': []})),
    (2, 400, 'patch', ('jar', 2, {'cookies': []})),
    
    #   All cookie creations should be valid
    (2, 201, 'post', ('cookie', {})),
    (2, 201, 'post', ('cookie', {'jar': 1})),

    #   Removing jar with cookies is also not allowed 
    (2, 400, 'delete', ('jar', 1)),
    (2, 400, 'delete', ('jar', 1)),
)

@pytest.mark.parametrize("mod_nr, expected_status, method, args", params)
def test_writable_1(init_world, get_client, mod_nr, expected_status, method, args):
    #   INIT
    init_world(cookies.dm)
    func_name = 'set_writable_{}'.format(mod_nr)
    eval(func_name)()
    client = get_client()
    
    #   TEST
    data, status, headers = getattr(client, method)(*args)
    assert status == expected_status

@pytest.mark.parametrize("status,method,args", [
    (400, 'patch', ('male', 1, {'wife': 2})),
    (400, 'patch', ('male', 1, {'wife': None})),
    (400, 'patch', ('male', 1, {'wife': 1})),

    (200, 'get', ('male', 1)),
    (400, 'delete', ('female', 1)),

    (201, 'post', ('male', {'name': 't1'})),
    (400, 'post', ('female', {'name': 't1', 'husband': 1})),
    (400, 'post', ('male', {'name': 't1', 'wife': 1})),
])
def test_male_wife(init_world, get_client, status, method, args):
    init_world(family.dm)
    client = get_client()

    #   Modify datamodel
    dm().object('male').field('wife')._writable = False

    assert getattr(client, method)(*args)[1] == status

@pytest.mark.parametrize("status,method,args", [
    (400, 'patch', ('male', 1, {'children': [1, 2]})),
    (400, 'patch', ('male', 1, {'children': []})),
    (400, 'patch', ('male', 1, {'children': [{'name': 'child_4'}]})),

    (200, 'get', ('male', 1)),
    (400, 'delete', ('child', 1)),

    (201, 'post', ('male', {'name': 't1'})),
    (201, 'post', ('child', {'name': 't1', 'mother': 1})),
    (400, 'post', ('child', {'name': 't1', 'father': 1})),
    (400, 'post', ('male', {'name': 't1', 'children': [{'name': 'ccc1'}]})),
    (400, 'post', ('male', {'name': 't1', 'children': [1]})),
])
def test_male_children(init_world, get_client, status, method, args):
    init_world(family.dm)
    client = get_client()

    #   Modify datamodel
    dm().object('male').field('children')._writable = False

    assert getattr(client, method)(*args)[1] == status
