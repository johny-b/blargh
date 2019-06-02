'''Test instance deletion.'''

from blargh.engine import world
from example import family, cookies

from .helpers.delete_data import expected_delete_data

import pytest
@pytest.mark.parametrize("data_id, deletions", [
    (1, [('male', 1)]),
    (2, [('child', 1)]),
    (3, [('child', 1), ('female', 2)]),
    (4, [('child', 1), ('female', 2), ('female', 1)]),
    (5, [('child', 1), ('female', 2), ('female', 1), ('male', 1)]),
    (6, [('child', 1), ('female', 2), ('female', 1), ('male', 1), ('child', 3)]),
    (7, [('child', 1), ('female', 2), ('female', 1), ('male', 1), ('child', 3), ('child', 2)]),
    (8, [('child', 1), ('female', 2), ('female', 1), ('male', 1), ('child', 3), ('child', 2), ('male', 2)]),
])
def test_api_delete_family(init_world, get_client, deletions, data_id):
    init_world(family.dm)
    client = get_client()

    for name, id_ in deletions:
        client.delete(name, id_)

    expected_data = expected_delete_data(data_id)

    assert world().data() == expected_data

@pytest.mark.parametrize("data_id, deletions", [
    (9, [('cookie', 1)]),
    (10, [('jar', 1)]),
    (11, [('jar', 2)]),
    (12, [('jar', 1), ('jar', 2)]),
])
def test_api_delete_cookies(init_world, get_client, deletions, data_id):
    init_world(cookies.dm)
    client = get_client()

    for name, id_ in deletions:
        client.delete(name, id_)

    expected_data = expected_delete_data(data_id)

    assert world().data() == expected_data
