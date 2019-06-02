'''
test "raw" update
'''

from blargh.engine import world
from ..helpers.common import related

from example import family
    
def all_instances():
    i = []
    for instances in world()._current_instances.values():
        for instance in instances.values():
            i.append(instance)
    return i

def change_husband(female_id, new_husband_id, op_target, write):
    '''
    Set new husband NEW_HUSBAND_ID for female defined by FEMALE_ID.
    This might be done in two ways:
        A) OP_TARGET == 'female'    - female's husband is changed
        B) OP_TARGET == 'husband'   - male's wife is changed

    If WRITE is False, change is made and instances that should have changed are returned.
    If WRITE is True, change is made, written, and fresh instances are returned.
    '''
    world().begin()
    female = world().get_instance('female', female_id)
    old_husband = related(female, 'husband')
    new_husband = world().get_instance('male', new_husband_id)
    old_wife = related(new_husband, 'wife')

    if op_target == 'female':
        female.update(dict(husband=new_husband_id))
    elif op_target == 'husband':
        new_husband.update(dict(wife=female_id))

    if write:
        old_husband_id = old_husband.id()
        old_wife_id = old_wife.id()
        
        world().write()
        world().commit()
        
        world().begin()
        female, new_husband, old_husband, old_wife = world().get_instance('female', female_id), \
            world().get_instance('male', new_husband_id), world().get_instance('male', old_husband_id), \
            world().get_instance('female', old_wife_id)
    return female, new_husband, old_husband, old_wife

def change_father(child_id, new_father_id, op_target, write):
    '''
    Set new father NEW_FATHER_ID for child defined by CHILD_ID.
    This might be done in two ways:
        A) OP_TARGET == 'child'     - child's 'father' attribute is changed
        B) OP_TARGET == 'father'    - child is added to new_father's children

    If WRITE is False, change is made and instances that should have changed are returned.
    If WRITE is True, change is made, written, and fresh instances are returned.
    '''
    world().begin()
    child = world().get_instance('child', child_id)
    old_father = related(child, 'father')
    new_father = world().get_instance('male', new_father_id)

    if op_target == 'child':
        child.update(dict(father=new_father_id))
    elif op_target == 'father':
        #   add to new father
        new_father_children = list(related(new_father, 'children'))
        new_father_children.append(child)
        new_father.update(dict(children=new_father_children))

    if write:
        old_father_id = old_father.id()
        
        world().write()
        world().commit()
        
        world().begin()
        child, old_father, new_father = world().get_instance('child', child_id), \
            world().get_instance('male', old_father_id), world().get_instance('male', new_father_id)

    return child, old_father, new_father

def test_update_father_1(init_world):
    init_world(family.dm)
    child, old_father, new_father = change_father(1, 2, 'child', False)

    assert related(child, 'father') == new_father
    assert child in related(new_father, 'children')
    assert child not in related(old_father, 'children')
    
    #   Check changed
    for i in all_instances():
        if i in (child, new_father, old_father):
            assert i.changed() is True
        else:
            print(i.repr(1))
            assert i.changed() is False

def test_update_father_2(init_world):
    init_world(family.dm)
    child, old_father, new_father = change_father(1, 2, 'child', True)

    assert related(child, 'father') == new_father
    assert child in related(new_father, 'children')
    assert child not in related(old_father, 'children')

def test_update_father_3(init_world):
    init_world(family.dm)
    child, old_father, new_father = change_father(1, 2, 'father', False)

    #   Check values
    assert related(child, 'father') == new_father
    assert child in related(new_father, 'children')
    assert child not in related(old_father, 'children')
    
    #   Check changed
    for i in all_instances():
        if i in (child, new_father, old_father):
            assert i.changed() is True
        else:
            assert i.changed() is False

def test_update_father_4(init_world):
    init_world(family.dm)
    child, old_father, new_father = change_father(1, 2, 'father', True)

    assert related(child, 'father') == new_father
    assert child in related(new_father, 'children')
    # assert child not in related(old_father, 'children')

def test_update_husband_1(init_world):
    init_world(family.dm)
    female, new_husband, old_husband, old_wife = change_husband(1, 2, 'female', False)

    #   Check values
    assert related(female, 'husband') == new_husband
    assert related(new_husband, 'wife') == female
    assert related(old_husband, 'wife') is None
    assert related(old_wife, 'husband') is None
    
    #   Check changed
    for i in all_instances():
        if i in (female, new_husband, old_husband, old_wife):
            assert i.changed() is True
        else:
            assert i.changed() is False

def test_update_husband_2(init_world):
    init_world(family.dm)
    female, new_husband, old_husband, old_wife = change_husband(1, 2, 'female', True)

    assert related(female, 'husband') == new_husband
    assert related(new_husband, 'wife') == female
    assert related(old_husband, 'wife') is None
    assert related(old_wife, 'husband') is None

def test_update_husband_3(init_world):
    init_world(family.dm)
    female, new_husband, old_husband, old_wife = change_husband(1, 2, 'husband', False)

    #   Check values
    assert related(female, 'husband') == new_husband
    assert related(new_husband, 'wife') == female
    assert related(old_husband, 'wife') is None
    assert related(old_wife, 'husband') is None

    #   Check changed
    for i in all_instances():
        if i in (female, new_husband, old_husband, old_wife):
            assert i.changed() is True
        else:
            assert i.changed() is False

def test_update_husband_4(init_world):
    init_world(family.dm)
    female, new_husband, old_husband, old_wife = change_husband(1, 2, 'husband', True)
    
    assert related(female, 'husband') == new_husband
    assert related(new_husband, 'wife') == female
    assert related(old_husband, 'wife') is None
    assert related(old_wife, 'husband') is None

def test_rename(init_world):
    init_world(family.dm)
    world().begin()
    for obj_name in ('male', 'female', 'child'):
        new_name = 'new_name_for_{}'.format(obj_name)
        obj_1 = world().get_instance(obj_name, 1)
        obj_1.update(dict(name=new_name))

        #   Check instance value
        assert obj_1.repr(1)['name'] == new_name

        #   Check written value
        world().write()
        obj_1 = world().get_instance(obj_name, 1)
        assert obj_1.repr(1)['name'] == new_name

    #   Check all writes for new world
    for obj_name in ('male', 'female', 'child'):
        expected_name = 'new_name_for_{}'.format(obj_name)
        obj_1 = world().get_instance(obj_name, 1)
        assert obj_1.repr(1)['name'] == expected_name
