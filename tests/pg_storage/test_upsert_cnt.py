'''
Test if blargh.engine.storage.pg.query.upsert() is called only when database change is necesary.
'''

from example import family
from blargh import engine
from tests.helpers.blargh_config import init_pg_world
from collections import defaultdict
import pytest

params = [
    ('post', ('child', {'name': 'c4'}), {'child': 1}),
    ('post', ('child', {'father': 1, 'name': 'c4'}), {'child': 1}),
    ('post', ('child', {'mother': 1, 'father': 1, 'name': 'c4'}), {'child': 1}),
    
    ('put', ('child', 4, {'name': 'c4'}), {'child': 1}),
    ('put', ('child', 4, {'father': 1, 'name': 'c4'}), {'child': 1}),
    ('put', ('child', 4, {'mother': 1, 'father': 1, 'name': 'c4'}), {'child': 1}),

    ('patch', ('male', 1, {'wife': 2}), {'female': 2}),
    ('patch', ('male', 1, {'wife': None}), {'female': 1}),
    ('patch', ('male', 1, {'children': []}), {'child': 2}),
    ('patch', ('male', 2, {'children': []}), {'child': 1}),
    ('patch', ('male', 1, {'name': 'aa'}), {'male': 1}),

    ('patch', ('female', 1, {'husband': 1}), {}),
    ('patch', ('female', 1, {'husband': 2}), {'female': 2}),
    ('patch', ('female', 1, {'husband': None}), {'female': 1}),
    ('patch', ('female', 1, {'name': 'aa'}), {'female': 1}),

    ('patch', ('child', 1, {'father': 1}), {}),
    ('patch', ('child', 1, {'father': 2}), {'child': 1}),
    ('patch', ('child', 1, {'father': 2, 'mother': 2}), {'child': 1}),
    ('patch', ('child', 1, {'name': 'xx'}), {'child': 1}),

    ('delete', ('male', 1), {'female': 1, 'child': 2}),
    ('delete', ('male', 2), {'female': 1, 'child': 1}),
    ('delete', ('female', 1), {'child': 1}),
    ('delete', ('female', 2), {'child': 2}),
    ('delete', ('child', 1), {}),

    ('get', ('child',), {}),
    ('get', ('child', 1), {}),
]


@pytest.mark.parametrize("method,args,expected_cnts", params)
def test_api_expected(get_client, method, args, expected_cnts):
    #   Init
    init_pg_world(family.dm)
    client = get_client()
    
    #   Modify storage.pg.Query.upsert() to make it count it's calls per resource type
    cnts = defaultdict(int)
    
    def wrap_create_storage(create_storage):
        def wrapped_create_storage(*args, **kwargs):
            storage = create_storage(*args, **kwargs)

            def wrap_upsert(f):
                def wrapped_upsert(*args, **kwargs):
                    table_name = args[0]
                    cnts[table_name] += 1
                    return f(*args, **kwargs)
                return wrapped_upsert

            storage._q.upsert = wrap_upsert(storage._q.upsert)
            return storage
        return wrapped_create_storage

    engine.config._config['create_storage'] = wrap_create_storage(engine.config._config['create_storage'])

    #   Test
    data, status, headers = getattr(client, method)(*args)
    
    assert str(status).startswith('2')
    assert dict(cnts) == expected_cnts
