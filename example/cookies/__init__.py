from .data_model import dm
from . import create
from .pg_schema import pg_schema_sql

def world_data(storage_name):
    if storage_name in ['DictStorage', 'PickledDictStorage']:
        return {
            'jar': {1: {'id': 1, 'cookies': [1, 2]},
                    2: {'id': 2, 'cookies': [3]}},
            'cookie': {1: {'id': 1, 'jar': 1, 'type': 'biscuit'},
                       2: {'id': 2, 'jar': 1, 'type': 'muffin'},
                       3: {'id': 3, 'jar': 2, 'type': 'shortbread'}}}
    elif storage_name == 'PGStorage':
        return {
            'jar': [(1,), (2,)],
            'cookie': [(1, 1, 'biscuit'), 
                       (2, 1, 'muffin'), 
                       (3, 2, 'shortbread')]}

    raise Exception("Unknown data for storage {}".format(storage_name))

