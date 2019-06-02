'''
Test scalar field default value
'''
from blargh.engine import dm
from example import cookies

def test_api_expected(init_world, get_client):
    init_world(cookies.dm)
    client = get_client()

    #   Check before change
    data, status, headers = client.post('cookie', {})
    assert status == 201
    assert 'type' not in data
    data, status, headers = client.post('cookie', {'type': 'muffin'})
    assert status == 201
    assert data['type'] == 'muffin'
    
    #   Set default
    dm().object('cookie').field('type').default = 'donut'
    
    #   Check after change
    data, status, headers = client.post('cookie', {})
    assert status == 201
    assert data['type'] == 'donut'

    data, status, headers = client.post('cookie', {'type': 'muffin'})
    assert status == 201
    assert data['type'] == 'muffin'

    data, status, headers = client.post('cookie', {'type': None})
    assert status == 201
    assert 'type' not in data
