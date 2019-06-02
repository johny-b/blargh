from blargh import engine
import os
import copy
import psycopg2
from example import family, cookies

from .test_clients import BaseApiClient, FlaskClient, BaseApiClientAuth, FlaskClientAuth

import pytest

'''
client = ClientClass()
client.get(RESOURCE, id_=None, filter=None, depth=None)
client.post(RESOURCE, object_or_list_of_objects)
client.patch(RESOURCE, id_, object)
client.put(RESOURCE, id_, object)
client.delete(RESOURCE, id_)
'''

def get_base_api_client(auth_required=False):
    if auth_required:
        return BaseApiClientAuth()
    else:
        return BaseApiClient()

def get_flask_client(auth_required=False):
    if auth_required:
        return FlaskClientAuth()
    else:
        return FlaskClient()


test_clients = [
    get_base_api_client,
    get_flask_client
]

def world_data():
    '''
    Returns expected data for current world, based on
        *   world's datamodel name
        *   example.*.world_data() function
    '''
    d = eval(engine.dm().name)
    return d.world_data(type(engine.world().storage).__name__)

def fill_world(create_function):
    def default_create_function():
        from importlib import import_module
        from blargh.engine import dm
        dm_name = dm().name
        module_name = 'example.{}.create'.format(dm_name)
        create = import_module(module_name)
        return create.__all__[0]

    if create_function is None:
        create_function = default_create_function()
    create_function()

    #   create_function commits changes, and after commit
    #   world (sometimes) is not usable, so here we recreate it
    engine.init_world()
     
def _init_world(dm, create_storage):
    #   in case anything messed up our data model
    #   (currently api/flask does)
    import copy
    copied_dm = copy.deepcopy(dm)
    engine.setup(dm=copied_dm, create_storage=create_storage)

def init_dict_world(dm, create_function=None):
    data = {}
    
    storage = engine.DictStorage(data)

    _init_world(dm, storage)
    fill_world(create_function)

def init_pickled_dict_world(dm, create_function=None):
    fname = 'tests/_dict_storage'
    try:
        os.remove(fname)
    except OSError:
        pass
    
    def storage():
        return engine.PickledDictStorage(fname)

    _init_world(dm, storage)
    fill_world(create_function)

def pg_connstr():
    return os.environ.get('PGS_CONNSTR')

def init_pg_world(dm, create_function=None):
    #   Initialize connection
    connstr = pg_connstr()
    if connstr is None:
        pytest.skip("env variable PGS_CONNSTR is not set -> PGStorage is not tested")
    connection = psycopg2.connect(connstr)
        
    #   Prepare temporary schema
    create_schema_sql = eval(dm.name).pg_schema_sql
    connection.cursor().execute('SET search_path TO pg_temp')
    connection.cursor().execute(create_schema_sql)
    connection.commit()
    
    #   Find temp schema name
    cur = connection.cursor()
    cur.execute('SELECT nspname FROM pg_namespace WHERE oid = pg_my_temp_schema()')
    schema_name = cur.fetchone()[0]

    #   Create & fill PG World with this connection
    def storage():
        return engine.PGStorage(connection, schema_name)

    _init_world(dm, storage)
    fill_world(create_function)


#   Each test will be run once per listed function
init_world_functions = [
    init_dict_world,
    init_pickled_dict_world,
    init_pg_world
]

#   curently this is not used anywhere
tested_data = [family, cookies]

def modify_expected_data(data, client):
    '''
    DATA is expected data for some test.

    We usually want to define one expected data per single test,
    but "real" expected result might differ for different clients.

    New data, really expected for this CLIENT, is returned.
    '''

    def add_flask_urls(d):
        #   (TODO?) ugly modification of 'expected' urls
        if type(d) is dict and 'url' in d:
            if d['url'].find('http://localhost/api') == -1:
                d['url'] = 'http://localhost/api/' + d['url']
            for el in d.values():
                add_flask_urls(el)
        elif type(d) is list:
            for el in d:
                add_flask_urls(el)
    data = copy.deepcopy(data)
    if type(client).__name__ == 'FlaskClient':
        add_flask_urls(data)
    return data
