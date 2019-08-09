'''
Test 
    *   limit=X in GET on a collection
    *   sort=[list_of_columns] in GET on a collection
'''
import pytest
from example import family
from blargh.engine import dm

params = (
    ([], {'limit': 0}),
    ([1], {'limit': 1}),
    ([1, 2], {'limit': 2}),
    ([1, 2, 3], {'limit': 3}),
    ([1, 2, 3], {'limit': 4}),
    ([1, 2, 3], {'sort': ['id']}),
    ([3, 2, 1], {'sort': ['-id']}),
    ([1, 3, 2], {'sort': ['dad']}),
    ([2, 1, 3], {'sort': ['-dad']}),
    ([2, 3, 1], {'sort': ['-dad', '-id']}),
    ([1, 3, 2], {'sort': ['dad', 'mother']}),
    ([3, 1, 2], {'sort': ['dad', '-mother']}),
    ([1, 2], {'sort': [], 'limit': 2}),
    ([3], {'sort': ['-id'], 'limit': 1}),
    ([3, 1], {'sort': ['dad', '-mother'], 'limit': 2}),
    ([1], {'filter_': {'dad': 1}, 'limit': 1, 'sort': ['mother']}),
    ([3], {'filter_': {'dad': 1}, 'limit': 1, 'sort': ['-mother']}),
)
@pytest.mark.parametrize('ids, kwargs', params)
def test_sort_and_limit(init_world, get_client, ids, kwargs):
    client = prepare(init_world, get_client)

    data, status_code, _ = client.get('child', depth=0, **kwargs)

    assert status_code == 200
    assert data == ids

def prepare(init_world, get_client):
    init_world(family.dm)
    client = get_client()

    #   sorting uses external names so it would be nice to have at least one different from internal name
    dm().object('child').field('father').ext_name = 'dad'

    return client
