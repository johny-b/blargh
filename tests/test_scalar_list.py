'''
Test lists stored as Scalar fields
'''

from example import cookies
from blargh import engine
from blargh.data_model.fields import Scalar

import pytest

@pytest.mark.parametrize("method, args, ingredients", (
    ('post', (), ['sugar', 'flour']),
    ('post', (), []),
    ('patch', (1,), ['sugar', 'flour']),
    ('patch', (1,), []),
))
def test_api_expected(init_world, get_client, method, args, ingredients):
    init_world(cookies.dm)
    client = get_client()

    #   Cookie field gets 'ingredients' text[] field
    engine.dm().object('cookie').add_field(Scalar('ingredients', default=[], type_=list))
    if issubclass(type(engine.world().storage), engine.PGStorage):
        engine.world().storage._q._conn.cursor().execute('''
            ALTER TABLE cookie ADD COLUMN ingredients text[];
        ''')

    #   Set ingredients
    data, status, headers = getattr(client, method)('cookie', *args, {'ingredients': ingredients})
    assert str(status).startswith('2')
    assert data['ingredients'] == ingredients

    #   Second check
    data, status, headers = client.get('cookie', data['id'])
    assert status == 200
    assert data['ingredients'] == ingredients
