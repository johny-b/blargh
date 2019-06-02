'''
Test if 
    *   only changed instances are written to the storage
    *   instances marked as "changed" really changed

this is tested by counting calls to world().storage.save().

Note: some storages could skip save(), if they notice that nothing changed.
This should be tested separately.
'''

from example import family
from blargh import engine
from collections import defaultdict
import pytest

params = [
    ('post', ('child', {'name': 'c4'}), {'child': 1}),
    ('post', ('child', {'father': 1, 'name': 'c4'}), {'child': 1, 'male': 1}),
    ('post', ('child', {'mother': 1, 'father': 1, 'name': 'c4'}), {'child': 1, 'male': 1, 'female': 1}),
    
    ('put', ('child', 4, {'name': 'c4'}), {'child': 1}),
    ('put', ('child', 4, {'father': 1, 'name': 'c4'}), {'child': 1, 'male': 1}),
    ('put', ('child', 4, {'mother': 1, 'father': 1, 'name': 'c4'}), {'child': 1, 'male': 1, 'female': 1}),

    #   Note differences between the same post and patch
    ('patch', ('male', 1, {'wife': 2}), {'male': 2, 'female': 2}),
    ('put',   ('male', 1, {'wife': 2}), {'male': 2, 'female': 2, 'child': 2}),              # noqa: E241
    ('patch', ('male', 1, {'wife': None}), {'male': 1, 'female': 1}),
    ('put',   ('male', 1, {'wife': None}), {'male': 1, 'female': 1, 'child': 2}),           # noqa: E241
    ('patch', ('male', 1, {'name': 'aa'}), {'male': 1}),
    ('put',   ('male', 1, {'name': 'aa'}), {'male': 1, 'female': 1, 'child': 2}),           # noqa: E241
    ('patch', ('male', 1, {'children': [2]}), {'male': 2, 'child': 3}),
    ('put',   ('male', 1, {'children': [2]}), {'male': 2, 'female': 1, 'child': 3}),        # noqa: E241
    ('patch', ('male', 1, {'children': [{}]}), {'male': 1, 'child': 3}),
    ('put',   ('male', 1, {'children': [{}]}), {'male': 1, 'female': 1, 'child': 3}),       # noqa: E241
    ('patch', ('male', 1, {'children': [2, {}]}), {'male': 2, 'child': 4}),
    ('put',   ('male', 1, {'children': [2, {}]}), {'male': 2, 'female': 1, 'child': 4}),    # noqa: E241

    ('delete', ('male', 1), {'female': 1, 'child': 2}),
    ('delete', ('child', 1), {'female': 1, 'male': 1}),

    ('get', ('child',), {}),
    ('get', ('child', 1), {}),
]


@pytest.mark.parametrize("method,args,expected_cnts", params)
def test_api_expected(init_world, get_client, method, args, expected_cnts):
    #   Init
    init_world(family.dm)
    client = get_client()
    
    #   Modify storage.save() to make it count it's calls per resource type
    cnts = defaultdict(int)
    
    def wrap_create_storage(create_storage):
        def wrapped_create_storage(*args, **kwargs):
            storage = create_storage(*args, **kwargs)

            def wrap_save(save):
                def wrapped_save(*args, **kwargs):
                    instance = args[0]
                    cnts[instance.model.name] += 1
                    return save(*args, **kwargs)
                return wrapped_save

            storage.save = wrap_save(storage.save)
            return storage
        return wrapped_create_storage
    engine.config._config['create_storage'] = wrap_create_storage(engine.config._config['create_storage'])

    #   Test
    data, status, headers = getattr(client, method)(*args)
    
    assert str(status).startswith('2')
    assert dict(cnts) == expected_cnts
