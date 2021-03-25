'''
blargh.engine.storage.pg.Query class can be extended in many ways,
modyfying selects/upserts/deleted to user needs.

Modifications tested here:
    *   Additional read-only resource shelf, stored in a strange way somewhere else
    *   Query that allows only creating donuts
'''


from example import cookies
from tests.helpers.blargh_config import init_pg_world
import pytest

from copy import deepcopy
from blargh import engine
from blargh import exceptions
from blargh.data_model.fields import Scalar, Rel

#   USED BY BOTH
def set_query_class(query_cls):
    '''
    Make tester use CLS as query
    '''
    def wrap_storage(f):
        def wrapped_storage(*args, **kwargs):
            old_storage = f(*args, **kwargs)
            new_storage = engine.PGStorage(old_storage._conn, old_storage._schema, query_cls=query_cls)
            return new_storage
        return wrapped_storage

    engine.config._config['create_storage'] = wrap_storage(engine.config._config['create_storage'])


#   WITH SHELF
shelf_select = '''
WITH 
values (id, position) AS (
    VALUES (1, 'top'), (2, 'bottom')
)
SELECT  *
FROM    values
'''

class ReadonlyResource(exceptions.e400):
    code = 'resource_is_readonly'

#   expected error message
shelf_is_readonly = {'error': {'code': 'RESOURCE_IS_READONLY', 'details': {'object_name': 'shelf'}}}

class WithShelf(engine.storage.pg.Query):
    def table_columns(self, name):
        if name == 'shelf':
            return ('id', 'position')
        return super().table_columns(name)

    def _select_all_sql(self, name):
        if name == 'shelf':
            return shelf_select
        return super()._select_all_sql(name)

    #   NOTE: upsert/delete are not necesary (this will raise e400 either way),
    #         but this way it is clearer
    def upsert(self, name, data):
        if name == 'shelf':
            raise ReadonlyResource(object_name='shelf')
        return super().upsert(name, data)

    def delete(self, name, pkey_val):
        if name == 'shelf':
            raise ReadonlyResource(object_name='shelf')
        return super().upsert(name, pkey_val)

    def default_pkey_expr(self, name, column_name):
        if name == 'shelf':
            raise ReadonlyResource(object_name='shelf')
        return super().default_pkey_expr(name, column_name)


def init_cookies_with_shelf():
    #   1.  Change data model
    dm = deepcopy(cookies.dm)
    shelf = dm.create_object('shelf')
    shelf.add_field(Scalar('id', pkey=True, type_=int))
    shelf.add_field(Scalar('position', pkey=False))

    jar = dm.object('jar')
    shelf.add_field(Rel('jars', stores=jar, multi=True))
    dm.object('jar').add_field(Rel('shelf', stores=shelf, multi=False))

    dm.connect(shelf, 'jars', jar, 'shelf')

    #   2.  Init world
    init_pg_world(dm)

    #   3.  Modify jar table,
    conn = engine.world().storage._conn
    conn.cursor().execute('''
        ALTER TABLE jar ADD COLUMN shelf integer CHECK (shelf IN (1, 2))
    ''')
    conn.commit()

    #   4.  Set new class
    set_query_class(WithShelf)

@pytest.mark.parametrize("method, expected_status, args, kwargs, expected_data", (
    #   GET should work as usual
    ('get', 200, ('shelf',), {}, [{'id': 1, 'position': 'top', 'jars': []},
                                  {'id': 2, 'position': 'bottom', 'jars': []}]),
    ('get', 200, ('shelf',), dict(depth=0), [1, 2]),
    ('get', 200, ('shelf', 2), {}, {'id': 2, 'position': 'bottom', 'jars': []}),
    ('get', 200, ('shelf',), dict(filter_={'position': 'top'}), [{'id': 1, 'position': 'top', 'jars': []}]),

    ('get', 400, ('shelf',), dict(filter_={'jars': []}), None),  # no searching by multi rel fields

    #   PATCHing shelf/jar relation is allowed in both ways
    ('patch', 200, ('jar', 1, {'shelf': 1}), {}, {'id': 1, 'cookies': [1, 2], 'shelf': 1}),
    ('patch', 200, ('shelf', 1, {'jars': [1, 2]}), {}, {'id': 1, 'position': 'top', 'jars': [1, 2]}),

    #   POSTING fresh jars on shelves is also possible in both ways
    ('post', 201, ('jar', {'shelf': 1}), {}, {'id': 3, 'cookies': [], 'shelf': 1}),
    ('patch', 200, ('shelf', 2, {'jars': [{}, {}]}), {}, {'id': 2, 'position': 'bottom', 'jars': [3, 4]}),

    #   PUTing jars is fine as well
    ('put', 201, ('jar', 3, {'shelf': 2}), {}, {'id': 3, 'cookies': [], 'shelf': 2}),

    #   POST/PUT/DELETE/PATCH on "stored" shelf field are not allowed
    ('patch', 400, ('shelf', 1, {'position': 'middle'}), {}, shelf_is_readonly),
    ('post', 400, ('shelf', {'position': 'middle'}), {}, shelf_is_readonly),
    ('put', 400, ('shelf', 1, {'position': 'middle'}), {}, shelf_is_readonly),
    ('put', 400, ('shelf', 3, {'position': 'middle'}), {}, shelf_is_readonly),
    ('delete', 400, ('shelf', 1), {}, shelf_is_readonly),
    ('delete', 404, ('shelf', 4), {}, None),  # 404 goes first
))
def test_shelf_1(get_client, method, expected_status, args, kwargs, expected_data):
    '''
    Test "simple" shelf case - always starting from basic cookies situation,
    test_shelf_2 tests jars already on shelves
    '''
    init_cookies_with_shelf()
    client = get_client()

    data, status, headers = getattr(client, method)(*args, **kwargs)

    assert status == expected_status

    if expected_data is not None:
        assert data == expected_data


@pytest.mark.parametrize("method, expected_status, args, kwargs, expected_data", (
    #   GET
    ('get', 200, ('shelf',), {}, [{'id': 1, 'position': 'top', 'jars': [1]},
                                  {'id': 2, 'position': 'bottom', 'jars': [2]}]),
    ('get', 200, ('shelf', 1), dict(depth=2),
        {'id': 1, 'position': 'top', 'jars': [{'id': 1, 'cookies': [1, 2], 'shelf': 1}]}),

    #   Add another jar to shelf
    ('patch', 200, ('shelf', 1, {'jars': [1, {}]}), {}, {'id': 1, 'position': 'top', 'jars': [1, 3]}),

    #   Remove jar
    ('patch', 200, ('shelf', 1, {'jars': []}), {}, {'id': 1, 'position': 'top', 'jars': []}),
    ('patch', 200, ('jar', 2, {'shelf': None}), {}, {'id': 2, 'cookies': [3]}),
))
def test_shelf_2(get_client, method, expected_status, args, kwargs, expected_data):
    '''
    Test with jars already on shelves
    '''
    init_cookies_with_shelf()
    client = get_client()

    #   Put jars on shelves
    assert client.patch('jar', 1, {'shelf': 1})[1] == 200
    assert client.patch('jar', 2, {'shelf': 2})[1] == 200

    #   Test
    data, status, headers = getattr(client, method)(*args, **kwargs)

    assert status == expected_status

    if expected_data is not None:
        assert data == expected_data

# #   ONLY DONUTS
# not_a_donut = "THIS IS NOT A DONUT!!!"
# class OnlyDonuts(engine.storage.pg.Query):
#     def upsert(self, name, data):
#         if 'type' in data and data['type'] != 'donut':
#             raise exceptions.e400(not_a_donut)
#         return super().upsert(name, data)
#
#
# @pytest.mark.parametrize("method, expected_status, args", (
#     ('post', 201, ('cookie', {'type': 'donut'})),
#     ('post', 400, ('cookie', {'type': 'not_a_donut'})),
#     ('post', 201, ('jar', {'cookies': [{}, {}]})),
#     ('post', 201, ('jar', {'cookies': [{'type': 'donut'}, {'type': 'donut'}, {}]})),
#     ('post', 400, ('jar', {'cookies': [{'type': 'donut'}, {'type': 'not_a_donut'}, {}]})),
#     ('patch', 200, ('cookie', 1, {'type': 'donut'})),
#     ('patch', 400, ('cookie', 1, {'type': 'not_a_donut'})),
# ))
# def test_only_donuts(get_client, method, expected_status, args):
#     init_pg_world(cookies.dm)
#     client = get_client()
#     set_query_class(OnlyDonuts)
#
#     data, status, headers = getattr(client, method)(*args)
#
#     assert status == expected_status
#
#     if status == 400:
#         assert data == {'msg': not_a_donut}
