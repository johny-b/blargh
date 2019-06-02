import psycopg2
import psycopg2.extras

class Query():
    '''Helper class for pg_schema_import'''
    def __init__(self, conn):
        self._conn = conn

    def get_rel_data(self, table_schema, table_name, column_name):
        '''
        COLUMN_NAME is a foreign key column defined in TABLE_SCHEMA.TABLE_NAME.

        Returns all data required to create relationship defined by
        column COLUMN_NAME of TABLE_SCHEMA.TABLE_NAME:
        {
            'other_name':  object referenced by FOREIGN KEY (we assume it is the same TABLE_SCHEMA)
            'this_card':   cardinality of TABLE_SCHEMA.TABLE_NAME
            'other_card':  cardinality of TABLE_SCHEMA.other_name
            'cascade':     True/False - are rows from TABLE_SCHEMA.TABLE_NAME cascade deleted?
        }
        
        cardinalities are  '?'/'1'/'*' (could be also '+', but it is never returned)
        '''
        q = query_str['get_rel_data'] 
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(q, {'table_schema': table_schema, 'table_name': table_name, 'column_name': column_name})
        return cur.fetchall()[0]

    def get_table_names_in_schema(self, table_schema):
        '''Returns names of all tables in schema SCHEMA_NAME'''
        q = query_str['get_table_names_in_schema']
        cur = self._conn.cursor()
        cur.execute(q, (table_schema,))
        return [row[0] for row in cur.fetchall()]

    def get_columns_data(self, table_schema, table_name):
        '''
        For each column of table SCHEMA_NAME.TABLE_NAME return its:
            * name
            * fkey: true if it is a FOREIGN KEY column
            * pkey: true if it is a PRIMARY KEY column
        '''
        q = query_str['get_columns_data'] 
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(q, {'table_schema': table_schema, 'table_name': table_name})
        data = cur.fetchall()
        
        #   Now in each data row, second element is a Postgresql type ('integer', 'text' etc),
        #   we need to convert it to python type (int, str etc). There is for sure a pretty way of
        #   doing this, since psycopg2 does it all the time, here the simplest possible solution is implemented
        #   - we cast 1 to given PG type and check returned python type.
        cur = self._conn.cursor()
        for row in data:
            cur.execute('SELECT 1::' + row['type'])
            row['type'] = type(cur.fetchone()[0])

        return data
        

#   To keep SQL as separate from python code as possible
query_str = {}
query_str['get_columns_data'] = '''
WITH
column_names AS (
    SELECT  column_name AS name, 
            data_type
    FROM    information_schema.columns
    WHERE   table_schema = %(table_schema)s
        AND table_name   = %(table_name)s
),
pkey_names AS (
    SELECT  a.attname AS name
    FROM    pg_index i
    JOIN    pg_attribute a ON a.attrelid = i.indrelid
                         AND a.attnum = ANY(i.indkey)
    WHERE   replace(i.indrelid::regclass::text, '"', '') = %(table_schema)s || '.' || %(table_name)s
        AND i.indisprimary
),
fkey_names AS (
    WITH table_fk AS (
        SELECT pg_get_constraintdef(c.oid) AS fk_def
        FROM   pg_constraint c
        WHERE  contype IN ('f')
            AND    replace(conrelid::regclass::text, '"', '') = %(table_schema)s || '.' || %(table_name)s
    )
    SELECT  (regexp_matches(fk_def, '^FOREIGN KEY \(\"?(\w+)\"?\).+$'))[1] AS name
    FROM    table_fk
)
SELECT  cn.name,
        data_type AS type,
        pn.name IS NOT NULL AS pkey,
        fn.name IS NOT NULL AS fkey
FROM    column_names cn
LEFT
JOIN    pkey_names   pn
    ON  cn.name = pn.name
LEFT
JOIN    fkey_names   fn
    ON  cn.name = fn.name
'''

query_str['get_rel_data'] = '''
WITH
constraint_def AS (
    SELECT  pg_get_constraintdef(c.oid) AS constraint_def,
            contype
    FROM    pg_constraint c
    WHERE   contype IN ('f', 'u')
        AND replace(conrelid::regclass::text, '"', '') = %(table_schema)s || '.' || %(table_name)s
),
other_name AS (
    SELECT  (regexp_matches(constraint_def, 
                'FOREIGN KEY \(\"?' || %(column_name)s || '\"?\) REFERENCES ' || 
                 %(table_schema)s || '\.\"?(\w+)\"?\(\w+\)'
            ))[1] AS other_name
    FROM    constraint_def
    WHERE   contype = 'f'
),
is_unique AS (
    WITH
    unique_constraints AS (
        SELECT  constraint_def
        FROM    constraint_def
        WHERE   contype = 'u'
            --  we care only abount one-column constraints
            --  (chr(37)) is percent sign, written this way to avoid psycopg2 problems
            AND constraint_def LIKE chr(37) || '(' || %(column_name)s || ')' || chr(37)
    )
    SELECT  exists(SELECT 1 FROM unique_constraints) AS is_unique
),
is_nullable AS (
    SELECT  bool(is_nullable) AS is_nullable
    FROM    information_schema.columns
    WHERE   table_schema = %(table_schema)s
        AND table_name   = %(table_name)s
        AND column_name  = %(column_name)s
),
is_cascade AS (
    SELECT  constraint_def ~* 'CASCADE' AS cascade
    FROM    constraint_def
    WHERE   contype = 'f'
),
card AS (
    SELECT  CASE WHEN is_unique
                THEN    '?'
                ELSE    '*'
            END AS this_card,
            CASE WHEN is_nullable
                THEN    '?'
                ELSE    '1'
            END AS other_card
    FROM    is_unique, is_nullable
)
SELECT  *
FROM    other_name, card, is_cascade
'''

query_str['get_table_names_in_schema'] = '''
SELECT  table_name 
FROM    information_schema.tables 
WHERE   table_schema = %s
'''
