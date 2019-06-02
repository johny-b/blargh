'''
Ensure that for existing objects PUT and PATCH work differently.

Note: only BaseApiClient is tested, to avoid fighting with 'url' column
for FlaskClient computed outside of request context blablabla.
This simplifies test, but should be good enough - PUT and PATCH differences
should be in the engine itself.
'''

from example import family
from blargh import engine
import pytest
from blargh.data_model import fields
from .helpers.test_clients import BaseApiClient

params = [
    ('child', 1, {'name': 'new_name'}),
    ('child', 1, {'father': 1}),
    ('child', 1, {'father': 2}),
    ('child', 1, {'father': 1, 'mother': 1}),
    ('male', 1, {'wife': 2}),
    ('male', 1, {'children': []}),
    ('male', 1, {'children': [], 'wife': 2}),
    ('female', 1, {'husband': 2}),
    ('female', 1, {'children': []}),
    ('female', 1, {'children': [], 'husband': 2}),
]


@pytest.mark.parametrize("resource, id_, arg_data", params)
def test_put_patch_diff(init_world, resource, id_, arg_data):
    init_world(family.dm)
    client = BaseApiClient()

    #   1.  Expected PATCH result - GET with depth == 1 updated with arg_data
    patch_data = client.get(resource, id_, depth=1)[0]
    patch_data.update(arg_data)

    #   2.  Expected PUT result:
    #       *   arg_data
    #       *   pkey column
    #       *   all calc fields
    #       *   empty list for all multi rel fields
    put_data = arg_data.copy()
    put_data[engine.dm().object(resource).pkey_field().ext_name] = id_
    world = engine.world()
    world.begin()
    instance = world.get_instance(resource, id_)
    world.rollback()
    for field, val in instance.field_values():
        if type(field) is fields.Calc:
            repr_val = val.repr()
            if repr_val is not None:
                put_data[field.ext_name] = repr_val
        elif field.rel and field.multi:
            put_data[field.ext_name] = []

    #   3.  Test if this test makes any sense (just to be sure, this would indicate serious problems)
    assert patch_data != put_data

    #   4.  Test PATCH (twice - second PUT should change nothing)
    for i in (0, 1):
        for data, status, headers in (client.patch(resource, id_, arg_data), client.get(resource, id_)):
            assert status == 200
            assert data == patch_data

    #   5.  Test PUT (twice - second PUT should change nothing)
    for i in (0, 1):
        for data, status, headers in (client.put(resource, id_, arg_data), client.get(resource, id_)):
            assert str(status).startswith('2')
            assert data == put_data
