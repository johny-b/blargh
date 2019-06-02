from blargh.engine import Engine, world_transaction

def create_api_1():
    Engine.post('jar', {})
    Engine.post('jar', {})
    Engine.post('cookie', {'type': 'biscuit', 'jar': 1})
    Engine.post('cookie', {'type': 'muffin', 'jar': 1})
    Engine.post('cookie', {'type': 'shortbread', 'jar': 2})

@world_transaction
def create_raw_1(w):
    #   Create cookies & jars
    j_1 = w.new_instance('jar')
    j_2 = w.new_instance('jar')
    c_1 = w.new_instance('cookie')
    c_2 = w.new_instance('cookie')
    c_3 = w.new_instance('cookie')

    #   Set types
    c_1.update(dict(type='biscuit'))
    c_2.update(dict(type='muffin'))
    c_3.update(dict(type='shortbread'))
   
    #   Put cookies in jars
    j_1.update(dict(cookies=[c_1, c_2]))
    j_2.update(dict(cookies=[c_3]))

@world_transaction
def create_raw_2(w):
    #   Create cookies & jars
    j_1 = w.new_instance('jar')
    j_2 = w.new_instance('jar')
    c_1 = w.new_instance('cookie')
    c_2 = w.new_instance('cookie')
    c_3 = w.new_instance('cookie')

    #   Set types
    c_1.update(dict(type='biscuit'))
    c_2.update(dict(type='muffin'))
    c_3.update(dict(type='shortbread'))
    
    #   Put cookies in jars
    c_1.update(dict(jar=j_1))
    c_2.update(dict(jar=j_1))
    c_3.update(dict(jar=j_2))


__all__ = [create_raw_1, create_raw_2, create_api_1]
