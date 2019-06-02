_config = {}
_worlds = {}

conf = {
    'max_retry_cnt': 2,
}

from os import getpid

def init_world():
    from .world_cls import World
    pid = getpid()
    create_storage = _config['create_storage']
    _worlds[pid] = World(dm(), create_storage())

    return world()

def world():
    pid = getpid()
    world = _worlds.get(pid)
    return world

def dm():
    return _config['dm']

def setup(dm, create_storage):
    '''
    :param dm: data model
    :param create_storage: function returning a Storage object,
                           or just a Storage object (wrapped here in a function)
    
    blargh initialization
    
    '''
    if callable(create_storage):
        create_storage_func = create_storage
    else:
        create_storage_func = lambda: create_storage  # noqa: E731

    _config['dm'] = dm
    _config['create_storage'] = create_storage_func
