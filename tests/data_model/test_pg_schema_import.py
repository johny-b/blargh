'''
IN: connection args & name of schema
OUT: DataModel matching schema
'''

from example import cookies, family

from tests.helpers.blargh_config import pg_connstr
from blargh.data_model import PGSchemaImport, fields
from copy import deepcopy

import pytest
import psycopg2

def schema_sql_2_dm(schema_sql, dm_name):
    '''
    IN: code creating postgresql schema and expected datamodel name
    OUT: datamodel created using PGSchemaImport
    '''
    #   Connection
    connstr = pg_connstr()
    if connstr is None:
        pytest.skip()
    conn = psycopg2.connect(connstr)

    #   Create schema
    conn.autocommit = 0
    schema_name = '_blargh_test_schema'

    #   1.  search_path is set to avoid collision with other tables in public schema
    #   2.  search_path is reset to public, because PGSchemaImport does not work for
    #       first schema in search_path (possible TODO)
    #   3.  temp schema is not used because it could be somehow different when messing
    #       with internal tables (don't know if is, but could), and this will never
    #       be used on temp schemas
    def cleanup():
        conn.rollback()
        conn.close()

    conn.cursor().execute('''
        CREATE SCHEMA       ''' + schema_name + ''';
        SET search_path TO  ''' + schema_name + ''';
        ''' + schema_sql + ''';
        SET search_path TO public;
    ''', {'schema_name': schema_name})

    #   Create data model
    try:
        dm = PGSchemaImport(conn, schema_name).data_model()
    except Exception as e:
        cleanup()
        raise e
    cleanup()

    #   Modify name
    assert dm.name == schema_name
    dm.name = dm_name

    return dm

def create_tested_dm(dm):
    '''
    Ugly function creating copy of DM that should match sql_schema_2_dm result,
    i.e. it removes all calc fields.
    '''
    tested_dm = deepcopy(dm)

    #   Remove calc fields
    for obj in tested_dm._objects.values():
        obj._fields = [f for f in obj._fields if type(f) is not fields.Calc]

    #   This is quite ugly
    if tested_dm.name == 'family':
        tested_dm.object('female').field('children').ext_name = 'mother_of'
        tested_dm.object('female').field('children').name = 'mother_of'
        tested_dm.object('male').field('wife').ext_name = 'husband_of'
        tested_dm.object('male').field('wife').name = 'husband_of'
        tested_dm.object('male').field('children').ext_name = 'father_of'
        tested_dm.object('male').field('children').name = 'father_of'

    return tested_dm

def cascade_cookies():
    '''
    Prepare test data for cookies with cascade delete
    '''
    sql = cookies.pg_schema_sql + '''; 
ALTER TABLE cookie
DROP CONSTRAINT cookie_jar_fkey,
ADD CONSTRAINT cookie_jar_fkey 
    FOREIGN KEY (jar) 
    REFERENCES jar(id) 
    ON DELETE CASCADE
    DEFERRABLE
;'''
    dm = deepcopy(cookies.dm)
    dm.object('cookie').field('jar').cascade = True
    return sql, dm

@pytest.mark.parametrize("schema_sql, dm", (
    (cookies.pg_schema_sql, cookies.dm),
    (family.pg_schema_sql, family.dm),
    cascade_cookies(),
))
def test_pg_schema_import(schema_sql, dm):
    #   Modify tested_dm to match expected created_dm (i.e. calc fields need to be removed)
    #   (just after we have removed calc fields - there are no calc fields in the database schema)
    tested_dm = create_tested_dm(dm)

    #   And this is created datamodel
    pg_schema_dm = schema_sql_2_dm(schema_sql, tested_dm.name)

    #   Test
    assert pg_schema_dm == tested_dm
