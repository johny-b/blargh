import pytest
from tests.auth.pg_storage_user_id.helpers import init_cookies_with_user_id

############
#   POST   #
############
@pytest.mark.parametrize("resource", ('cookie', 'jar'))
def test_put_new_object(get_client, resource):
    '''
    POST new object, test if 
        *   the same user can GET it 
        *   other user can't GET it
    '''
    init_cookies_with_user_id()
    client = get_client(auth_required=True)

    #   1.  Login as user 1
    client.login({'user_id': 1})

    #   2.  Create object
    data, status, headers = client.post(resource, {})
    assert status == 201
    id_ = data['id']

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
