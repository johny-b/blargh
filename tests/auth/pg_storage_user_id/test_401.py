'''
Without authentication every call should return 401
'''

import pytest
from tests.auth.pg_storage_user_id.helpers import init_cookies_with_user_id

args = (
    ('get', 'jar'),
    ('get', 'jar', 1),
    ('post', 'jar', {}),
    ('patch', 'jar', 1, {}),
    ('delete', 'jar', 1),
    ('put', 'jar', 1, {}),
)
@pytest.mark.parametrize("args", args)
def test_401_no_auth_1(get_client, args):
    '''
    401 without authentication
    '''
    init_cookies_with_user_id()
    client = get_client(auth_required=True)

    method, *other_args = args
    data, status, headers = getattr(client, method)(*other_args)

    assert status == 401

@pytest.mark.parametrize("args", args)
def test_401_no_auth_2(get_client, args):
    '''
    401 without authentication (client does not permit logging in)
    '''
    init_cookies_with_user_id()
    client = get_client()

    method, *other_args = args
    data, status, headers = getattr(client, method)(*other_args)

    assert status == 401

@pytest.mark.parametrize("args", args)
def test_401_empty_auth(get_client, args):
    '''
    401 with empty authentication
    '''
    init_cookies_with_user_id()
    client = get_client(auth_required=True)
    client.login({})

    method, *other_args = args
    data, status, headers = getattr(client, method)(*other_args)

    assert status == 401

@pytest.mark.parametrize("args", args)
def test_401_incorrect_auth(get_client, args):
    '''
    401 with empty authentication
    '''
    init_cookies_with_user_id()
    client = get_client(auth_required=True)
    client.login({'some': 'thing'})

    method, *other_args = args
    data, status, headers = getattr(client, method)(*other_args)

    assert status == 401
