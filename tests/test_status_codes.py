from example import family, cookies
import pytest

'''
Test 404 status code (and 200 for similar, but correct requests)
'''
@pytest.mark.parametrize("status,method,args", [
    (404, 'get', ('jar', 3)),
    (404, 'get', ('cookie', 4)),
    (404, 'delete', ('jar', 3)),
    (404, 'delete', ('cookie', 4)),
    (404, 'patch', ('jar', 3, {})),
    (404, 'patch', ('cookie', 4, {})),
    (404, 'post', ('cookie', {'jar': 3})),
    (404, 'post', ('jar', {'cookies': [1, 4]})),
    (200, 'get', ('jar', 2)),
    (200, 'get', ('cookie', 3)),
    (200, 'delete', ('jar', 2)),
    (200, 'delete', ('cookie', 2)),
    (200, 'patch', ('jar', 2, {})),
    (200, 'patch', ('cookie', 2, {})),
    (201, 'post', ('cookie', {'jar': 1})),
    (201, 'post', ('jar', {'cookies': [1, 2]})),

    #   Integer ID passed as text should also be accepted
    (201, 'post', ('cookie', {'jar': "1"})),
    (201, 'post', ('jar', {'cookies': ["1", "2"]})),
])
def test_404(init_world, get_client, status, method, args):
    init_world(cookies.dm)
    client = get_client()

    assert getattr(client, method)(*args)[1] == status

@pytest.mark.parametrize("args", [
    ('child', 2),
    ('male', 1),
    ('female', 1),
])
def test_repeated_delete_404(init_world, get_client, args):
    init_world(family.dm)
    client = get_client()

    assert client.delete(*args)[1] == 200
    assert client.delete(*args)[1] == 404

def test_delete_404_family(init_world, get_client):
    init_world(family.dm)
    client = get_client()

    for name in ('child', 'male', 'female'):
        for id_ in range(1, 5):
            for attempt in range(0, 2):
                if attempt > 0 or ((id_ > 2 and name != 'child') or (id_ > 3)):
                    assert client.delete(name, id_)[1] == 404
                else:
                    assert client.delete(name, id_)[1] == 200


@pytest.mark.parametrize("test_set, resource, kwargs", [
    (family, 'male', {'filter_': {'children': [1, 2]}}),
    (family, 'female', {'filter_': {'children': [2]}}),
    (cookies, 'jar', {'filter_': {'cookies': [1]}}),
    (cookies, 'jar', {'filter_': {'cookies': []}}),
])
def test_multi_rel_field_400(init_world, get_client, test_set, resource, kwargs):
    '''
    Search is allowed only on scalar fields, 
    and single rel fields
    '''
    init_world(test_set.dm)
    client = get_client()

    data, code, headers = client.get(resource, **kwargs)
    assert code == 400
