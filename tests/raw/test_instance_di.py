'''
Instance class should be easly modified via World.set_instance_class()
'''

from blargh.engine import Instance, world
from example import cookies

class FirstJarCookieInstance(Instance):
    def __init__(self, model, data={}, first=False):
        self.is_first = first
        super().__init__(model, data, first)

    def update(self, d):
        d['jar'] = 1
        return super().update(d)

def get_instance_class(name):
    if name == 'cookie':
        return FirstJarCookieInstance
    return Instance


def test_1(init_world):
    init_world(cookies.dm, get_instance_class=get_instance_class)
    world().begin()
    cookie = world().new_instance('cookie')
    assert cookie.is_first

def test_2(init_world):
    init_world(cookies.dm, get_instance_class=get_instance_class)
    world().begin()
    cookie = world().get_instance('cookie', 1)
    assert not cookie.is_first

def test_3(init_world):
    init_world(cookies.dm, get_instance_class=get_instance_class)
    world().begin()
    cookie = world().get_instance('cookie', 1)
    cookie.update({'jar': 2})
    assert type(cookie) is FirstJarCookieInstance
    assert cookie.repr(1)['jar'] == 1

def test_4(init_world):
    init_world(cookies.dm, get_instance_class=get_instance_class)
    world().begin()
    jar = world().get_instance('jar', 1)
    assert type(jar) is Instance
