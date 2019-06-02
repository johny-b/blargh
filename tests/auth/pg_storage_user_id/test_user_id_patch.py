import pytest
from tests.auth.pg_storage_user_id.helpers import init_cookies_with_user_id

#############
#   PATCH   #
#############
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
def test_patch(get_client, user_id, resource, id_, expected_status):
    '''
    Test if PATCH on object returns correct status
    '''
    init_cookies_with_user_id()
    client = get_client(auth_required=True)
    client.login({'user_id': user_id})

    data, status, headers = client.patch(resource, id_, {})
    assert status == expected_status
