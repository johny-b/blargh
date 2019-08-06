'''
Test limit=X in GET on a collection
'''
import pytest
from example import family

@pytest.mark.parametrize('limit, ids', (
    (0, []),
    (1, [1]),
    (2, [1, 2]),
    (3, [1, 2, 3]),
    (4, [1, 2, 3]),
))
def test_limit(init_world, get_client, limit, ids):
    init_world(family.dm)
    client = get_client()

    data, status_code, _ = client.get('child', limit=limit, depth=0)

    assert status_code == 200
    assert data == ids
