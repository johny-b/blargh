'''
Test ext_name of a field
'''

from example import cookies
from blargh.engine import dm, world

def test_ext_name_get(init_world, get_client):
    #   1.  Init
    init_world(cookies.dm)
    client = get_client()

    #   2.  Set an ext_name
    dm().object('cookie').field('type').ext_name = 'Cookie Type'
    
    #   3.  Get data
    data, status, headers = client.get('cookie', 1)
    
    #   4.  Check
    assert 'Cookie Type' in data
    assert 'type' not in data

def test_ext_name_filter(init_world, get_client):
    #   1.  Init
    init_world(cookies.dm)
    client = get_client()

    #   2.  Set an ext_name
    dm().object('cookie').field('type').ext_name = 'Cookie Type'
    
    #   3.  Get data
    data, status, headers = client.get('cookie', filter_={'Cookie Type': 'biscuit'})
    
    #   4.  Check
    assert status == 200
    assert type(data) is list
    assert len(data) is 1

    #   5.  Check "bad" filter
    data, status, headers = client.get('cookie', filter_={'type': 'biscuit'})
    assert status == 400

def test_ext_name_post(init_world, get_client):
    #   1.  Init
    init_world(cookies.dm)
    client = get_client()

    #   2.  Set an ext_name
    dm().object('cookie').field('type').ext_name = 'Cookie Type'
    
    #   3.  Post data
    data, status, headers = client.post('cookie', {'Cookie Type': 'tasty'})
    
    #   4.  Check
    assert status == 201

    #   5.  Get created data
    data, status, headers = client.get('cookie', 4)

    #   6.  Check
    assert status == 200
    assert data['Cookie Type'] == 'tasty'
    
    #   7.  Post bad data
    data, status, headers = client.post('cookie', {'type': 'tasty'})

    #   8.  Check
    assert status == 400

def test_ext_name_put(init_world, get_client):
    #   1.  Init
    init_world(cookies.dm)
    client = get_client()

    #   2.  Set an ext_name
    dm().object('cookie').field('type').ext_name = 'Cookie Type'
    
    #   3.  Post data
    data, status, headers = client.put('cookie', 4, {'Cookie Type': 'tasty'})
    
    #   4.  Check
    assert status == 201

    #   5.  Get created data
    data, status, headers = client.get('cookie', 4)

    #   6.  Check
    assert status == 200
    assert data['Cookie Type'] == 'tasty'
    
    #   7.  Put bad data
    data, status, headers = client.put('cookie', 5, {'type': 'tasty'})

    #   8.  Check
    assert status == 400

def test_ext_name_patch(init_world, get_client):
    #   1.  Init
    init_world(cookies.dm)
    client = get_client()

    #   2.  Set an ext_name
    dm().object('cookie').field('type').ext_name = 'Cookie Type'
    
    #   3.  Post data
    data, status, headers = client.patch('cookie', 3, {'Cookie Type': 'tasty'})
    
    #   4.  Check
    assert status == 200

    #   5.  Get created data
    data, status, headers = client.get('cookie', 3)

    #   6.  Check
    assert status == 200
    assert data['Cookie Type'] == 'tasty'
    
    #   7.  Bad patch
    data, status, headers = client.patch('cookie', 3, {'type': 'tasty'})

    #   8.  Check
    assert status == 400

def test_ext_name_storage(init_world, get_client):
    '''
    ext_name should have no influence on stored data
    '''
    #   1.  Init
    init_world(cookies.dm)
    client = get_client()

    #   2.  Post
    data, status, headers = client.post('cookie', {'type': 'tasty'})
    id_ = data['id']
    stored_before = world().data()

    #   4.  Set an ext_name
    dm().object('cookie').field('type').ext_name = 'Cookie Type'
    
    #   5.  Put the same data, but using ext_name
    data, status, headers = client.put('cookie', id_, {'Cookie Type': 'tasty'})
    
    #   6.  Check
    assert stored_before == world().data()

