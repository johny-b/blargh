import pytest
from tests.auth.pg_storage_user_id.helpers import init_cookies_with_user_id

###########
#   GET   #
###########
@pytest.mark.parametrize("user_id, resource, expected_ids", (
    (1, 'cookie', [1, 2]),
    (2, 'cookie', [3]),
    (1, 'jar', [1]),
    (2, 'jar', [2]),
))
def test_get_1(get_client, user_id, resource, expected_ids):
    '''
    Test if GET on collection returns correct entities
    '''
    init_cookies_with_user_id()
    client = get_client(auth_required=True)
    client.login({'user_id': user_id})

    data, status, headers = client.get(resource, depth=0)
    assert status == 200
    assert data == expected_ids

@pytest.mark.parametrize("user_id, resource, id_, expected_status", (
    (1, 'cookie', 1, 200),
    (1, 'cookie', 2, 200),
    (1, 'cookie', 3, 404),
    (2, 'cookie', 1, 404),
    (2, 'cookie', 2, 404),
    (2, 'cookie', 3, 200),

    (1, 'jar', 1, 200),
    (1, 'jar', 2, 404),
    (2, 'jar', 1, 404),
    (2, 'jar', 2, 200),
))
def test_get_2(get_client, user_id, resource, id_, expected_status):
    '''
    Test if GET on object returns correct status
    '''
    init_cookies_with_user_id()
    client = get_client(auth_required=True)
    client.login({'user_id': user_id})

    data, status, headers = client.get(resource, id_)
    assert status == expected_status
