'''
Rel fields should accept default values.

Currently only not-connected fields may have non-empty defaults,
so here we test "fresh" relational fields.
'''

from example import family
from blargh.engine import dm, world, PGStorage
from blargh.data_model.fields import Rel

def test_single_default_1(init_world, get_client):
    '''
    Best Friend - always child 1
    '''
    init_world(family.dm)
    client = get_client()

    #   1.  Add best_friend field.
    child = dm().object('child')
    child.add_field(Rel('best_friend', stores=child, multi=False, default=1))
    
    #   If this is PG storage, we need to update database schema
    if issubclass(type(world().storage), PGStorage):
        conn = world().storage._conn
        conn.cursor().execute('ALTER TABLE child ADD COLUMN best_friend integer REFERENCES child(id) DEFERRABLE')
        conn.commit()

    #   2.  Post a child without best friend
    data, status, headers = client.post('child', {'name': 'c'})
    assert status == 201
    assert data['best_friend'] == 1

    #   3.  Post a child with best friend
    data, status, headers = client.post('child', {'name': 'c', 'best_friend': 2})
    assert status == 201
    assert data['best_friend'] == 2

def test_single_multi_2(init_world, get_client):
    '''
    Best Friend - new female named BLARGH (note: new anonymous child creates infinite recursion)
    '''
    init_world(family.dm)
    client = get_client()

    #   1.  Add best_friend field. New child's best friend is always child no 1.
    child = dm().object('child')
    child.add_field(Rel('best_friend', stores=dm().object('female'), multi=False, default={'name': 'BLARGH'}))
    
    #   If this is PG storage, we need to update database schema
    if issubclass(type(world().storage), PGStorage):
        conn = world().storage._conn
        conn.cursor().execute('ALTER TABLE child ADD COLUMN best_friend integer REFERENCES child(id) DEFERRABLE')
        conn.commit()

    #   2.  Post a child without best friend
    data, status, headers = client.post('child', {'name': 'c'})
    assert status == 201
    assert data['best_friend'] == 3

    #   3.  Check if name was saved
    data, status, headers = client.get('female', 3)
    assert status == 200
    assert data['name'] == 'BLARGH'

    #   4.  Post a child with best friend
    data, status, headers = client.post('child', {'name': 'c', 'best_friend': 2})
    assert status == 201
    assert data['best_friend'] == 2

def test_multi_default_1(init_world, get_client):
    '''
    friends - always childred 1 & 2
    '''
    init_world(family.dm)
    client = get_client()

    #   1.  Add best_friend field.
    child = dm().object('child')
    child.add_field(Rel('friends', stores=child, multi=True, default=[1, 2]))
    
    #   If this is PG storage, we need to update database schema
    if issubclass(type(world().storage), PGStorage):
        conn = world().storage._conn
        conn.cursor().execute('ALTER TABLE child ADD COLUMN friends integer[]')
        conn.commit()

    #   2.  Post a child without friends
    data, status, headers = client.post('child', {'name': 'c'})
    assert status == 201
    assert data['friends'] == [1, 2]

    #   3.  Post a child with friends
    data, status, headers = client.post('child', {'name': 'c', 'friends': [2, 3]})
    assert status == 201
    assert data['friends'] == [2, 3]

def test_multi_default_2(init_world, get_client):
    '''
    Friends - females named BLARGH and BLERGH
    '''
    init_world(family.dm)
    client = get_client()

    #   1.  Add friends field - two fresh females, BLARGH and BLERGH
    child = dm().object('child')
    child.add_field(Rel('friends', stores=dm().object('female'), multi=True, 
                    default=[{'name': 'BLARGH'}, {'name': 'BLERGH'}]))
    
    #   If this is PG storage, we need to update database schema
    if issubclass(type(world().storage), PGStorage):
        conn = world().storage._conn
        conn.cursor().execute('ALTER TABLE child ADD COLUMN friends integer[]')
        conn.commit()

    #   2.  Post a child without best friend
    data, status, headers = client.post('child', {'name': 'c'})
    assert status == 201
    assert data['friends'] == [3, 4]

    #   3.  Post a child with best friend
    data, status, headers = client.post('child', {'name': 'c', 'friends': [1, 2]})
    assert status == 201
    assert data['friends'] == [1, 2]
