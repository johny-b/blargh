from example import family
from time import sleep
from blargh import engine
import pytest
import multiprocessing as mp
from os import getpid
from tests.helpers.blargh_config import pg_connstr
import psycopg2
from copy import deepcopy
import importlib

from blargh.engine.storage.pg import pg_storage

schema_name = '_blargh_test_transactions'

def get_connection():
    connstr = pg_connstr()
    if connstr is None:
        pytest.skip("env variable PGS_CONNSTR is not set -> PGStorage is not tested")
    conn = psycopg2.connect(connstr)
    return conn

def prepare():
    #   Init connection
    conn = get_connection()

    #   Create test schema
    create_schema_sql = family.pg_schema_sql
    conn.cursor().execute('CREATE SCHEMA {}'.format(schema_name))
    conn.cursor().execute('SET search_path TO {}'.format(schema_name))
    conn.cursor().execute(create_schema_sql)
    conn.commit()

    #   Init world
    def create_storage():
        conn = get_connection()
        conn.cursor().execute('SET search_path TO {}'.format(schema_name))
        return pg_storage.PGStorage(conn, schema_name)

    engine.setup(dm=deepcopy(family.dm), create_storage=create_storage)

    #   Fill test schema
    create_func = family.create.create_api_1
    create_func()

    #   Modify PGStorage, to make it sleep a little before each load,
    #   to avoid very fast operations
    def wrap_load(load):
        def wrapped_load(*args, **kwargs):
            print("LOAD!", getpid(), args[1:3])
            sleep(0.002)
            return load(*args, **kwargs)
        return wrapped_load
    pg_storage.PGStorage.load = wrap_load(pg_storage.PGStorage.load)


def run_in_process(queue, client, method, args):
    def run(q):
        engine.init_world()
        data, status, headers = getattr(client, method)(*args)
        q.put(status)
        print(getpid(), status, data)

    p = mp.Process(target=run, args=(queue,))
    p.start()
    return p

@pytest.fixture(autouse=True)
def cleanup():
    yield

    #   Drop schema
    conn = engine.world().storage._conn
    conn.close()
    conn = get_connection()
    conn.cursor().execute('DROP SCHEMA IF EXISTS {} CASCADE'.format(schema_name))
    conn.commit()
    
    #   Reload PGStorage - remove code changes
    importlib.reload(pg_storage)
    
    
op1 = ('patch', ('child', 1, {'mother': 2}))
op2 = ('patch', ('child', 1, {'mother': None}))
op3 = ('put', ('female', 2, {'children': []}))
op4 = ('post', ('male', {'wife': 2}))


@pytest.mark.skipif(pg_connstr() is None, reason='Only tested for PGStorage')
@pytest.mark.parametrize("op1, op2, retry_cnt, success_cnt", (
    (op1, op2, -1, 1),   # retry_cnt below 0 should work just like 0
    (op1, op2, 0, 1),
    (op1, op2, 1, 2),
    (op1, op2, 2, 2),    # retry_cnt 2 changes nothing
    (op1, op3, 0, 1),
    (op1, op3, 1, 2),
    (op3, op4, 0, 1),
    (op3, op4, 1, 2),
))
def test_serializable(get_client, cleanup, op1, op2, retry_cnt, success_cnt):
    '''
    op1 and op2 are run concurrently, in separate processes.
    It is assumed:
        *   exactly one of them will fail, if max_retry_cnt is 0
        *   both will success if max_retry_cnt is 1
    '''

    prepare()
    client = get_client()
    
    engine.conf['max_retry_cnt'] = retry_cnt

    q = mp.Queue()

    p1 = run_in_process(q, client, *op1)
    p2 = run_in_process(q, client, *op2)

    p1.join()
    p2.join()
    
    [*statuses] = q.get_nowait(), q.get_nowait()

    assert len([s for s in statuses if 200 <= s < 300]) == success_cnt
