from blargh.engine import Engine, world_transaction

def create_api_1():
    Engine.post('male', {'name': 'm1'})
    Engine.post('male', {'name': 'm2'})
    Engine.post('female', {'name': 'f1'})
    Engine.post('female', {'name': 'f2'})
    Engine.post('child', {'name': 'c1'})
    Engine.post('child', {'name': 'c2'})
    Engine.post('child', {'name': 'c3'})

    Engine.patch('male', 1, {'wife': 1})
    Engine.patch('male', 2, {'wife': 2})
    Engine.patch('child', 1, {'mother': 1, 'father': 1})
    Engine.patch('child', 2, {'mother': 2, 'father': 2})
    Engine.patch('child', 3, {'mother': 2, 'father': 1})

def create_api_2():
    Engine.post('male', {'name': 'm1'})
    Engine.post('male', {'name': 'm2'})
    Engine.post('female', {'name': 'f1', 'husband': 1})
    Engine.post('female', {'name': 'f2', 'husband': 2})
    Engine.post('child', {'name': 'c1', 'father': 1, 'mother': 1})
    Engine.post('child', {'name': 'c2', 'father': 2, 'mother': 2})
    Engine.post('child', {'name': 'c3', 'father': 1, 'mother': 2})

def create_api_3():
    Engine.put('male', 1, {'name': 'm1'})
    Engine.put('male', 2, {'name': 'm2'})
    Engine.put('female', 1, {'name': 'f1', 'husband': 1})
    Engine.put('female', 2, {'name': 'f2', 'husband': 2})
    Engine.put('child', 1, {'name': 'c1', 'father': 1, 'mother': 1})
    Engine.put('child', 2, {'name': 'c2', 'father': 2, 'mother': 2})
    Engine.put('child', 3, {'name': 'c3', 'father': 1, 'mother': 2})

def create_api_4():
    Engine.post('male', [{}, {}])
    Engine.post('female', [{}, {}])
    Engine.post('child', [{}, {}, {}])

    Engine.patch('male', 1, {'wife': 1, 'name': 'm1'})
    Engine.patch('male', 2, {'wife': 2, 'name': 'm2'})
    Engine.patch('female', 1, {'name': 'f1'})
    Engine.patch('female', 2, {'name': 'f2'})
    Engine.patch('child', 1, {'name': 'c1', 'mother': 1, 'father': 1})
    Engine.patch('child', 2, {'name': 'c2', 'mother': 2, 'father': 2})
    Engine.patch('child', 3, {'name': 'c3', 'mother': 2, 'father': 1})

def create_api_5():
    #   Create m1, f1, c1
    Engine.post('male', {'name': 'm1', 
                         'children': [{'name': 'c1'}],
                         'wife': {'name': 'f1'}})

    #   Create m2, f2, c2
    Engine.post('male', {'name': 'm2', 
                         'children': [{'name': 'c2'}],
                         'wife': {'name': 'f2'}})

    #   Create c3 and add missing relationships
    Engine.patch('female', 2, {'children': [2, {'name': 'c3', 'father': 1}]})
    Engine.patch('female', 1, {'children': [1]})

@world_transaction
def create_raw_1(w):
    #   Create people
    m_1 = w.new_instance('male')
    m_2 = w.new_instance('male')
    f_1 = w.new_instance('female')
    f_2 = w.new_instance('female')
    c_1 = w.new_instance('child')
    c_2 = w.new_instance('child')
    c_3 = w.new_instance('child')

    #   Set names
    m_1.update(dict(name='m1'))
    m_2.update(dict(name='m2'))
    f_1.update(dict(name='f1'))
    f_2.update(dict(name='f2'))
    c_1.update(dict(name='c1'))
    c_2.update(dict(name='c2'))
    c_3.update(dict(name='c3'))
    
    #   Set marriages
    m_1.update(dict(wife=f_1))
    m_2.update(dict(wife=f_2))

    #   Set children (note: c_3 is cross-marriage))
    c_1.update(dict(father=m_1, mother=f_1))
    c_2.update(dict(father=m_2, mother=f_2))
    c_3.update(dict(father=m_1, mother=f_2))


__all__ = [create_raw_1, create_api_1, create_api_2, create_api_3, create_api_4, create_api_5]
