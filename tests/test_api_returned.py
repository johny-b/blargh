'''
Test returned values from post/patch/put/delete.
Get is in separate tests/test_get.py
'''

from example import family
from .helpers.blargh_config import modify_expected_data
import pytest

params = [
    ('post', 201, ('child', {'name': 'c4'}), {'id': 4, 'url': 'child/4', 'name': 'c4'}),
    ('post', 201, ('child', [{}, {}]), [{'id': 4, 'url': 'child/4'}, {'id': 5, 'url': 'child/5'}]),
    ('patch', 200, ('child', 1, {'name': 'zz'}), {'id': 1, 'url': 'child/1', 'name': 'zz', 'father': 1, 'mother': 1}),
    ('patch', 200, ('child', 1, {'father': 2}), {'id': 1, 'url': 'child/1', 'name': 'c1', 'mother': 1, 'father': 2}),
    ('put', 201, ('child', 7, {'name': 'c7'}), {'id': 7, 'url': 'child/7', 'name': 'c7'}),
    ('delete', 200, ('child', 2), None),

    #   post/put/patch creating other objects
    ('post', 201, ('male', {'name': 'm3', 'children': [{}, {}]}), 
        {'name': 'm3', 'id': 3, 'url': 'male/3', 'children': [4, 5]}),
    ('put', 201, ('male', 3, {'name': 'm3', 'children': [{}], 'wife': {}}), 
        {'name': 'm3', 'id': 3, 'url': 'male/3', 'children': [4], 'wife': 3}),
    ('patch', 200, ('male', 1, {'children': [{}], 'wife': {}}), 
        {'name': 'm1', 'id': 1, 'url': 'male/1', 'children': [4], 'wife': 3}),
    ('patch', 200, ('male', 1, {'children': [{'mother': 2}, {}, 1], 'wife': {}}), 
        {'name': 'm1', 'id': 1, 'url': 'male/1', 'children': [1, 4, 5], 'wife': 3}),
]


@pytest.mark.parametrize("method, expected_status, args, expected_data", params)
def test_api_expected(init_world, get_client, method, expected_status, args, expected_data):
    init_world(family.dm)
    client = get_client()
    expected_data = modify_expected_data(expected_data, client)

    data, status, headers = getattr(client, method)(*args)
    
    assert status == expected_status
    assert data == expected_data
