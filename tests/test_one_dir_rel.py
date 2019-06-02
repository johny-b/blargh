'''
All tested examples have 'connected' relationship fields - cookie knows it's jar, jar knows it's cookies, etc.

This is not required, Rel field without any connection makes perfect sense, but has serious downsides
- no changes propagate. I.e. if we want to move first cookie between first and second jar, when fields
are connected, we might either
    *   set cookie's jar
or
    *   add cookie to second jar's cookies
and achive the same result. Without connection - let's say, jar knows it's cookies, 
but cookie has no idea about it's jar - we need to perform two actions:
    *   remove cookie from first jar
    *   add cookie to the second jar
what's worse, currently there is no way of doing it in one call - this are two PATCHEs.

Anyway, this should work, so gets a test.
'''
from example import cookies
from copy import deepcopy
from blargh.data_model.fields import Scalar, Rel
from blargh.engine import world, PGStorage

def init_cookies_with_shelf_1(init_world):
    '''Add shelf to cookies datamodel. 
    Shelf knows it's jars, jar has no idea about shelf
    '''
    dm = deepcopy(cookies.dm)
    shelf = dm.create_object('shelf')
    shelf.add_field(Scalar('id', pkey=True, type_=int))
    shelf.add_field(Rel('jars', stores=dm.object('jar'), multi=True))

    init_world(dm)

    #   If this is PG storage, we need to update database schema
    if issubclass(type(world().storage), PGStorage):
        conn = world().storage._conn
        conn.cursor().execute('CREATE TABLE shelf (id serial PRIMARY KEY, jars integer[])')
        conn.commit()

def init_cookies_with_shelf_2(init_world):
    '''Add shelf to cookies datamodel. 
    Jar knows it's shelf, shelf has no idea about jars.
    '''
    dm = deepcopy(cookies.dm)
    shelf = dm.create_object('shelf')
    shelf.add_field(Scalar('id', pkey=True, type_=int))
    jar = dm.object('jar')
    jar.add_field(Rel('shelf', stores=shelf, multi=False))
    init_world(dm)
    
    #   If this is PG storage, we need to update database schema
    if issubclass(type(world().storage), PGStorage):
        conn = world().storage._conn
        conn.cursor().execute('CREATE TABLE shelf (id serial PRIMARY KEY)')
        conn.cursor().execute('ALTER TABLE jar ADD COLUMN shelf integer REFERENCES shelf(id)')
        conn.commit()

def test_one_dir_1(init_world, get_client):
    #   1.  Init world
    init_cookies_with_shelf_1(init_world)
    client = get_client()
    
    #   2.  Save current world state, for further comparisions
    world_data = world().data()

    #   3.  Create a shelf with both jars
    data, status, headers = client.put('shelf', 1, {'jars': [1, 2]})
    assert status == 201
    
    #   4.  Check if world data didn't change (except shelf)
    new_world_data = world().data()
    assert new_world_data['cookie'] == world_data['cookie']
    assert new_world_data['jar'] == world_data['jar']

    #   5.  Check if GET works as expected
    jar_1, status_1, headers = client.get('jar', 1, depth=1)
    jar_2, status_2, headers = client.get('jar', 2, depth=1)
    shelf, status_3, headers = client.get('shelf', 1, depth=2)
    assert status_1 == 200
    assert status_2 == 200
    assert status_3 == 200
    assert shelf['jars'] == [jar_1, jar_2]

    #   6.  Test 404
    shelf, status, headers = client.put('shelf', 2, {'jars': [3]})
    assert status == 404

def test_one_dir_2(init_world, get_client):
    #   1.  Init world
    init_cookies_with_shelf_2(init_world)
    client = get_client()

    #   2.  Create a shelf
    data, status, headers = client.put('shelf', 1, {})
    assert status == 201

    #   3.  Put first jar on a shelf
    data, status, headers = client.patch('jar', 1, {'shelf': 1})

    #   4.  Check if GET works as expected
    jar_1, status_1, headers = client.get('jar', 1, depth=2)
    jar_2, status_2, headers = client.get('jar', 2, depth=1)
    shelf, status_3, headers = client.get('shelf', 1, depth=1)
    assert status_1 == 200
    assert status_2 == 200
    assert status_3 == 200
    assert jar_1['shelf'] == shelf
    assert 'shelf' not in jar_2
    
    #   5.  Test 404
    data, status, headers = client.patch('jar', 1, {'shelf': 2})
    assert status == 404
