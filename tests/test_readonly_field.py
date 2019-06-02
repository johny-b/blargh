'''
If field is readonly, it should not be possible to send it by post/patch/put
'''

from blargh.engine import dm
from example import cookies
import pytest

@pytest.mark.parametrize("resource, data", [
    ('cookie', {'type': 'donut'}),
    ('jar', {'cookies': [{}]}),
    ('jar', {'cookies': [1]}),
])
def test_male_children(init_world, get_client, resource, data):
    init_world(cookies.dm)
    client = get_client()
    
    #   Check before changes
    assert client.post(resource, data)[1] == 201
    assert client.put(resource, 1, data)[1] == 201
    assert client.put(resource, 7, data)[1] == 201
    assert client.patch(resource, 1, data)[1] == 200
    assert client.patch(resource, 7, data)[1] == 200

    #   Modify datamodel
    field_name = list(data.keys())[0]
    dm().object(resource).field(field_name).readonly = True

    #   Check after changes
    assert client.post(resource, data)[1] == 400
    assert client.put(resource, 1, data)[1] == 400
    assert client.put(resource, 7, data)[1] == 400
    assert client.patch(resource, 1, data)[1] == 400
