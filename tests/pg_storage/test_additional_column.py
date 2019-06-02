'''
Test if everything works even when there are columns not included in the datamodel.
They should not be accessible in any way.
'''

from blargh.engine import world
from tests.helpers.blargh_config import init_pg_world
from example import cookies
import pytest

create_args = [
    #   POST
    (201, 'post', ({},)),
    (201, 'post', ({'jar': 1},)),
    (201, 'post', ({'type': 'donut'},)),
    (400, 'post', ({'weight': 77.77},)),

    #   PUT
    (201, 'put', (7, {})),
    (201, 'put', (7, {'jar': 1})),
    (201, 'put', (7, {'type': 'donut'})),
    (400, 'put', (7, {'weight': 77.77})),

    #   DELETE (no idea how this could be influenced, but just to be sure)
    (200, 'delete', (2,)),

    #   PATCH
    (200, 'patch', (2, {'type': 'donut'})),
    (400, 'patch', (2, {'weight': 22.22})),

    #   GET - tests filter only (TODO: test returned values)
    (200, 'get', {'filter_': {'type': 'shortbread'}}),
    (200, 'get', {'filter_': {'jar': 1}}),
    (400, 'get', {'filter_': {'weight': 11}}),
]

@pytest.mark.parametrize("status,method,args", create_args)
def test_cookies_with_weight(get_client, status, method, args):
    init_pg_world(cookies.dm)
    client = get_client()

    #   cookies column gets additional column datamodel knows nothing about
    conn = world().storage._conn
    conn.cursor().execute('ALTER TABLE cookie ADD COLUMN weight float DEFAULT 33.33')
    conn.commit()
    world().storage._q._table_columns_data = {}  # delete table info cache
    
    #   get has kwargs, other have args
    if method == 'get':
        assert getattr(client, method)('cookie', **args)[1] == status
    else:
        assert getattr(client, method)('cookie', *args)[1] == status

    #   whatever we did, it should never influence column not in the datamodel
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT weight FROM cookie")
    data = cur.fetchall()
    assert len(data) == 1
    assert data[0][0] == 33.33
