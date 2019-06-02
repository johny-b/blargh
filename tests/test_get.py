from .helpers.get import expected_get_data
from .helpers.blargh_config import init_dict_world, init_pg_world
from blargh.engine import world

from example import family, cookies
import pytest


'''
Test if there is no stupid internal GET cache (there once was)
'''
def test_get_cache(get_client):
    #   We use DictWorld only because we need to touch it's internals to imitate "other" application.
    init_dict_world(family.dm)
    client = get_client()

    #   1.  Initial check - first child should have name 'c1' (if has different, 
    #       something is seriously wrong and the rest of the test makes no sence)
    data, status_code, *headers = client.get('child', 1)
    assert data['name'] == 'c1'

    #   2.  Modify data, without any blargh interface (that could clear potential cache)
    world().storage._commited['child'][1]['name'] = 'new_c1_name'

    #   3.  Check
    data, status_code, *headers = client.get('child', 1)
    assert data['name'] == 'new_c1_name'


@pytest.mark.parametrize("method, args", (
    ('post', ('cookie', {})), 
    ('put', ('cookie', 1, {})),
    ('put', ('cookie', 7, {})),
))
def test_implicit_fields_post_put(get_client, method, args):
    '''
    Check if fields set in a implicit way after POST/PUT (i.e. database defaults) are returned
    '''
    #   INIT
    init_pg_world(cookies.dm)
    client = get_client()

    #   Add default column value
    world().storage._conn.cursor().execute('''
        ALTER TABLE cookie
            ALTER COLUMN jar SET DEFAULT 1;
    ''')
    data, status, headers = getattr(client, method)(*args)
    assert status == 201
    assert data['jar'] == 1


def test_implicit_fields_patch(get_client):
    '''
    Check if fields set in a implicit way after PATCH (i.e. by database triggers) are returned
    '''
    #   INIT
    init_pg_world(cookies.dm)
    client = get_client()

    #   Add trigger changing type after update
    world().storage._conn.cursor().execute('''
        CREATE FUNCTION pg_temp.new_cookie_type() RETURNS trigger AS $new_cookie_type$
        BEGIN
            NEW.type = 'type_set_by_trigger';
            RETURN NEW;
        END;
        $new_cookie_type$ LANGUAGE plpgsql;

        CREATE TRIGGER change_cookie_type
        BEFORE UPDATE ON pg_temp.cookie
        FOR EACH ROW EXECUTE PROCEDURE pg_temp.new_cookie_type();
    ''')

    #   Create fresh cookie
    data, status, headers = client.put('cookie', 4, {'type': 'donut'}) 
    assert status == 201
    assert data['type'] == 'donut'

    #   Make sure it's still a donut
    data, status, headers = client.get('cookie', 4)
    assert status == 200
    assert data['type'] == 'donut'

    #   Patch it with some data and check if we got triggered type
    data, status, headers = client.patch('cookie', 4, {'type': 'doesnt matter'})
    assert status == 200
    assert data['type'] == 'type_set_by_trigger'
    
    #   Make sure it's still a triggered type
    data, status, headers = client.get('cookie', 4)
    assert status == 200
    assert data['type'] == 'type_set_by_trigger'


'''
Test returned data
'''
get_params = [
    (1,   'child',  dict(id_=1, depth=0)),                                          # noqa: E241
    (2,   'child',  dict(id_=1, depth=1)),                                          # noqa: E241
    (3,   'child',  dict(id_=1, depth=2)),                                          # noqa: E241
    (4,   'child',  dict(id_=1, depth=3)),                                          # noqa: E241
    (5,   'child',  dict(id_=1, depth=4)),                                          # noqa: E241
    (6,   'child',  dict(depth=0)),                                                 # noqa: E241
    (7,   'child',  dict(depth=1)),                                                 # noqa: E241
    (8,   'child',  dict(filter_=dict(name='c1'))),                                 # noqa: E241
    (9,   'child',  dict(filter_=dict(name='NIEMA'))),                              # noqa: E241
    (10,  'female', dict(depth=1, filter_=dict(name='f1'))),                        # noqa: E241

    # Note: filter is 'id', but get param is 'id_' - this is intended, 'id' is an external name
    (11,  'female', dict(depth=1, filter_={'id': 2})),                              # noqa: E241

    (12,  'child',  dict(depth=0, filter_={'father': 1})),                          # noqa: E241
    (13,  'child',  dict(depth=0, filter_={'father': 1, 'name': 'c1'})),            # noqa: E241
    (14,  'child',  dict(depth=0, filter_={'father': 1, 'name': 'c2'})),            # noqa: E241
    (15,  'female', dict(depth=0, filter_={'name': 'f1'})),                         # noqa: E241
    (15,  'female', dict(depth=0, filter_={'husband': 1})),                         # noqa: E241
    (15,  'female', dict(depth=0, filter_={'husband': 1, 'name': 'f1'})),           # noqa: E241
    (15,  'female', dict(depth=0, filter_={'husband': 1, 'id': 1})),                # noqa: E241
    (15,  'female', dict(depth=0, filter_={'husband': 1, 'id': 1, 'name': 'f1'})),  # noqa: E241
    (0,   'female', dict(depth=0, filter_={'husband': 1, 'id': 1, 'name': 'f2'})),  # noqa: E241
    (0,   'female', dict(depth=0, filter_={'husband': 3})),                         # noqa: E241
    (0,   'female', dict(depth=0, filter_={'husband': 1, 'name': 'f2'})),           # noqa: E241
    (0,   'female', dict(depth=0, filter_={'husband': 1, 'id': 2})),                # noqa: E241
    (0,   'female', dict(depth=0, filter_={'husband': 1, 'id': 2})),                # noqa: E241
    (16,  'male',   dict(depth=0, filter_={'name': 'm1'})),                         # noqa: E241
    (16,  'male',   dict(depth=0, filter_={'wife': 1})),                            # noqa: E241
    (16,  'male',   dict(depth=0, filter_={'wife': 1, 'name': 'm1'})),              # noqa: E241
    (16,  'male',   dict(depth=0, filter_={'wife': 1, 'id': 1})),                   # noqa: E241
    (16,  'male',   dict(depth=0, filter_={'wife': 1, 'id': 1, 'name': 'm1'})),     # noqa: E241
    (0,   'male',   dict(depth=0, filter_={'wife': 1, 'id': 2, 'name': 'm1'})),     # noqa: E241
    (0,   'male',   dict(depth=0, filter_={'wife': 3})),                            # noqa: E241
    (0,   'male',   dict(depth=0, filter_={'wife': 1, 'name': 'm2'})),              # noqa: E241
    (0,   'male',   dict(depth=0, filter_={'wife': 1, 'id': 2})),                   # noqa: E241
    (17,  'child',  dict(depth=0, filter_={'father': 1, 'mother': 1})),             # noqa: E241
    (18,  'child',  dict(depth=0, filter_={'father': 1, 'mother': 2})),             # noqa: E241
    (19,  'child',  dict(depth=0, filter_={'father': 2, 'mother': 2})),             # noqa: E241
    (0,   'child',  dict(depth=0, filter_={'father': 2, 'mother': 1})),             # noqa: E241
    (0,   'child',  dict(depth=0, filter_={'father': 3, 'mother': 1})),             # noqa: E241
    (0,   'child',  dict(depth=0, filter_={'father': 1, 'mother': 3})),             # noqa: E241
]
@pytest.mark.parametrize("data_id, resource, kwargs", get_params)
def test_base_get_family(init_world, get_client, resource, kwargs, data_id):
    #   Init
    init_world(family.dm)
    client = get_client()

    #   Fetch tested data
    data, status_code, *headers = client.get(resource, **kwargs)

    #   Expected data
    expected_data = expected_get_data(data_id, client)

    #   Test
    assert status_code == 200
    assert data == expected_data
