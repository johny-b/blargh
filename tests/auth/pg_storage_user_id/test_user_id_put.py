import pytest
from tests.auth.pg_storage_user_id.helpers import init_cookies_with_user_id

###########
#   PUT   #
###########
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
def test_put_on_existing(get_client, user_id, resource, id_, expected_status):
    '''
    Test if PUT on existing object returns correct status
    '''
    init_cookies_with_user_id()
    client = get_client(auth_required=True)
    client.login({'user_id': user_id})

    data, status, headers = client.patch(resource, id_, {})
    assert status == expected_status


@pytest.mark.parametrize("resource, id_", (
    ('cookie', 7),
    ('jar', 7),
))
def test_put_new_object(get_client, resource, id_):
    '''
    PUT new object, test if 
        *   the same user can GET it 
        *   other user can't GET it
    '''
    init_cookies_with_user_id()
    client = get_client(auth_required=True)

    #   1.  Login as user 1
    client.login({'user_id': 1})

    #   2.  Create object
    data, status, headers = client.put(resource, id_, {})
    assert status == 201

    #   3.  Test if creator has access
    data, status, headers = client.get(resource, id_)
    assert status == 200

    #   4.  Test if not logged gets 401
    client.logout()
    data, status, headers = client.get(resource, id_)
    assert status == 401

    #   5.  Test if other user gets 404
    client.login({'user_id': 2})
    data, status, headers = client.get(resource, id_)
    assert status == 404

    #   6.  Test again correct user
    client.logout()
    client.login({'user_id': 1})
    data, status, headers = client.get(resource, id_)
    assert status == 200
