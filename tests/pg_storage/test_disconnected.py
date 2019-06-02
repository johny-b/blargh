'''
Test 500 in case of disconnected database
'''

from blargh.engine import world
from tests.helpers.blargh_config import init_pg_world
from example import cookies
import pytest

@pytest.mark.parametrize("method,args", [
    ('get', ('jar', 1)),
    ('delete', ('jar', 1)),
    ('post', ('jar', {})),
    ('put', ('jar', 1, {})),
    ('patch', ('jar', 1, {})),
])
def test_disconnected_database(get_client, method, args):
    init_pg_world(cookies.dm)
    client = get_client()

    world().storage._conn.close()
    assert getattr(client, method)(*args)[1] == 500
