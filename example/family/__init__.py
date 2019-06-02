from .data_model import dm
from . import create
from .pg_schema import pg_schema_sql

def world_data(storage_name):
    if storage_name in ['DictStorage', 'PickledDictStorage']:
        return {
            'child': {1: {'father': 1, 'id': 1, 'mother': 1, 'name': 'c1'},
                      2: {'father': 2, 'id': 2, 'mother': 2, 'name': 'c2'},
                      3: {'father': 1, 'id': 3, 'mother': 2, 'name': 'c3'}},
            'female': {1: {'children': [1], 'husband': 1, 'id': 1, 'name': 'f1'},
                       2: {'children': [2, 3], 'husband': 2, 'id': 2, 'name': 'f2'}},
            'male': {1: {'children': [1, 3], 'id': 1, 'name': 'm1', 'wife': 1},
                     2: {'children': [2], 'id': 2, 'name': 'm2', 'wife': 2}}}
    elif storage_name == 'PGStorage':
        return {
            'child': [(1, 'c1', 1, 1), 
                      (2, 'c2', 2, 2), 
                      (3, 'c3', 1, 2)],
            'female': [(1, 'f1', 1), 
                       (2, 'f2', 2)],
            'male': [(1, 'm1'), 
                     (2, 'm2')]}
    raise Exception("Unknown data for storage {}".format(storage_name))
