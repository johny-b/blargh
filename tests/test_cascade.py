'''
Test cascade=True for Rel fields.

Note: cascade=True for multi fields is not tested, because is forbidden.
'''

from example import family
from blargh.engine import dm

import pytest

@pytest.mark.parametrize("cascades, method, args, deleted", (
    #   Test irrelevant cascades
    ((('child', 'father'),), 'delete', ('female', 1), {'female': [1]}),
    ((('child', 'father'),), 'delete', ('child', 1), {'child': [1]}),

    #   Test single cascade field
    ((('child', 'father'),), 'delete', ('male', 1), {'male': [1], 'child': [1, 3]}),
    ((('child', 'father'),), 'delete', ('male', 2), {'male': [2], 'child': [2]}),
    ((('female', 'husband'),), 'delete', ('male', 1), {'male': [1], 'female': [1]}),
    ((('female', 'husband'),), 'delete', ('male', 2), {'male': [2], 'female': [2]}),
    
    #   Test multiple cascade fields
    ((('male', 'wife'), ('child', 'father')), 'delete', ('female', 1), {'female': [1], 'male': [1], 'child': [1, 3]}),
    ((('female', 'husband'), ('child', 'mother')), 'delete', ('male', 2), {'female': [2], 'male': [2], 'child': [2, 3]}),  # noqa: E501
    
    #   Test possible recursion problems
    ((('male', 'wife'), ('female', 'husband')), 'delete', ('male', 1), {'female': [1], 'male': [1]}),
    ((('male', 'wife'), ('female', 'husband')), 'delete', ('male', 2), {'female': [2], 'male': [2]}),
    ((('male', 'wife'), ('female', 'husband')), 'delete', ('female', 1), {'female': [1], 'male': [1]}),
    ((('male', 'wife'), ('female', 'husband')), 'delete', ('female', 2), {'female': [2], 'male': [2]}),
    
    #   Few more tests
    ((('male', 'wife'), ('child', 'father'), ('child', 'mother')), "delete", ('female', 2), {'female': [2], 'male': [2], 'child': [2, 3]}),  # noqa: E501
    ((('female', 'husband'), ('child', 'father'), ('child', 'mother')), "delete", ('male', 2), {'female': [2], 'male': [2], 'child': [2, 3]}),  # noqa: E501
    ((('female', 'husband'), ('child', 'father'), ('child', 'mother')), "delete", ('male', 1), {'female': [1], 'male': [1], 'child': [1, 3]}),  # noqa: E501

    #   And now for something completly different: check if PATCH/POST don't delete anything ...
    ((('child', 'father'),), 'patch', ('male', 1, {'children': []}), {}),
    ((('female', 'husband'),), 'patch', ('male', 1, {'wife': 2}), {}),
    ((('female', 'husband'),), 'post', ('female', {'husband': 1}), {}),

    #   .. but PUT does
    ((('male', 'wife'),), 'put', ('female', 1, {'husband': 2}), {'male': [1]}),
    ((('child', 'father'),), 'put', ('male', 1, {}), {'child': [1, 3]}),
    ((('child', 'father'), ('female', 'husband')), 'put', ('male', 1, {}), {'female': [1], 'child': [1, 3]}),

))
def test_cascade_father(init_world, get_client, cascades, method, args, deleted):
    #   Init
    init_world(family.dm)
    client = get_client()
    for obj_name, field_name in cascades:
        dm().object(obj_name).field(field_name).cascade = True
    
    #   Perform action (delete, probably)
    assert str(getattr(client, method)(*args)[1]).startswith('2')
    
    #   Check
    ids_map = {'male': [1, 2], 'female': [1, 2], 'child': [1, 2, 3]}
    for name, ids in ids_map.items():
        for id_ in ids:
            print(name, id_)
            status = client.get(name, id_)[1]
            expected_status = 404 if id_ in deleted.get(name, []) else 200
            assert status == expected_status
