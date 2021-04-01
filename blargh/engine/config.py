
from os import getpid
_config = {}
_worlds = {}

conf = {
    'max_retry_cnt': 2,
}


def init_world():
    from .world_cls import World
    pid = getpid()
    create_storage = _config['create_storage']
    _worlds[pid] = World(dm(), create_storage(), _config['get_instance_class'])

    return world()

def world():
    pid = getpid()
    world = _worlds.get(pid)
    return world

def dm():
    return _config['dm']

def default_get_instance_class(name):
    from .instance import Instance
    return Instance

def setup(dm, create_storage, get_instance_class=None):
    '''
    :param dm: data model
    :param create_storage: function returning a Storage object,
                           or just a Storage object (wrapped here in a function)

    blargh initialization

    '''
    if callable(create_storage):
        create_storage_func = create_storage
    else:
        def create_storage_func(): return create_storage  # noqa: E731

    if get_instance_class is None:
        get_instance_class = default_get_instance_class

    _config['dm'] = dm
    _config['create_storage'] = create_storage_func
    _config['get_instance_class'] = get_instance_class
