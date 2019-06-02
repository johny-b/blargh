'''
test NOT NULL columns
'''

from blargh.engine import world
from tests.helpers.blargh_config import init_pg_world
from example import cookies
import pytest

##############
#   PATCH    #
##############
patch_args = [
    #   no update
    (200, 1, {'jar': 1}, {'id': 1, 'jar': 1, 'type': 'biscuit'}),
    (200, 1, {'jar': 1, 'type': 'biscuit'}, {'id': 1, 'jar': 1, 'type': 'biscuit'}),
    (200, 1, {'type': 'biscuit'}, {'id': 1, 'jar': 1, 'type': 'biscuit'}),

    #   real update!
    (200, 1, {'jar': 2}, {'id': 1, 'jar': 2, 'type': 'biscuit'}),
    (200, 1, {'type': 'tasty'}, {'id': 1, 'jar': 1, 'type': 'tasty'}),
    (200, 1, {'jar': 1, 'type': 'tasty'}, {'id': 1, 'jar': 1, 'type': 'tasty'}),
    (200, 1, {'jar': 2, 'type': 'tasty'}, {'id': 1, 'jar': 2, 'type': 'tasty'}),
    (200, 1, {'jar': None}, {'id': 1, 'type': 'biscuit'}),
    (200, 1, {'jar': None, 'type': 'tasty'}, {'id': 1, 'type': 'tasty'}),
    (400, 1, {'jar': 2, 'type': None}, {'error': {
        'code': 'BAD_REQUEST', 
        'details': {'msg': 'null value in column "type" violates not-null constraint'}}}),
    (400, 1, {'type': None}, {'error': {
        'code': 'BAD_REQUEST', 
        'details': {'msg': 'null value in column "type" violates not-null constraint'}}}),
    (404, 1, {'jar': 3, 'type': 'tasty'}, {'error': {
        'code': 'OBJECT_DOES_NOT_EXIST', 'details': {'object_name': 'jar', 'object_id': 3}}}),

]

@pytest.mark.parametrize("expected_status,cookie_id,args,expected_data", patch_args)
def test_not_null_patch(get_client, expected_status, cookie_id, args, expected_data):
    init_pg_world(cookies.dm)
    client = get_client()

    #   from now on, we no longer accept cookies of unknown type
    conn = world().storage._conn
    conn.cursor().execute('ALTER TABLE cookie ALTER COLUMN type SET NOT NULL')
    conn.commit()

    data, status, headers = client.patch('cookie', cookie_id, args)
    assert status == expected_status
    print(data)
    if expected_data is not None:
        assert data == expected_data


################
#   POST/PUT   #
################
create_args = [
    (400, {}),
    (400, {'jar': 1}),
    (201, {'type': 'carrot pie'}),
    (201, {'jar': 1, 'type': 'carrot pie'}),

    #   Note: 'bad' jar ID is found earlier than (possible) not null violation,
    #   so 404 is returned instead of 400
    (404, {'jar': 7}),
    (404, {'jar': 7, 'type': 'amaretti'}),
]

@pytest.mark.parametrize("status,args", create_args)
def test_not_null_post(get_client, status, args):
    init_pg_world(cookies.dm)
    client = get_client()

    #   from now on, we no longer accept cookies of unknown type
    conn = world().storage._conn
    conn.cursor().execute('ALTER TABLE cookie ALTER COLUMN type SET NOT NULL')
    conn.commit()

    assert client.post('cookie', args)[1] == status

@pytest.mark.parametrize("status,args", create_args)
def test_not_null_put(get_client, status, args):
    init_pg_world(cookies.dm)
    client = get_client()

    #   from now on, we no longer accept cookies of unknown type
    conn = world().storage._conn
    conn.cursor().execute('ALTER TABLE cookie ALTER COLUMN type SET NOT NULL')
    conn.commit()
    
    assert client.put('cookie', 4, args)[1] == status


########################
#   NOT NULL DEFAULT   #
########################
create_args = [
    (201, {}),
    (201, {'jar': 1}),
]

@pytest.mark.parametrize("status,args", create_args)
def test_not_null_default(get_client, status, args):
    init_pg_world(cookies.dm)
    client = get_client()

    #   from now on, we no longer accept cookies of unknown type
    conn = world().storage._conn
    conn.cursor().execute('ALTER TABLE cookie ALTER COLUMN type SET NOT NULL')
    conn.cursor().execute("ALTER TABLE cookie ALTER COLUMN type SET DEFAULT 'butter cookie'")
    conn.commit()

    assert client.post('cookie', args)[1] == status
