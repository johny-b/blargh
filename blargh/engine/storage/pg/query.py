from psycopg2 import sql
import psycopg2.extras

class Query():
    '''Helper class for PGStorage'''
    def __init__(self, conn, schema, pkeys):
        self._conn = conn
        self._schema = schema
        self._pkeys = pkeys

        #   Some "internal" informations are cached here
        self._default_pkey_expr = {}
        self._table_columns_data = {}

    #   DELETE, UPSERT, SELECT: main methods used by PGStorage.
    def delete(self, name, pkey_val):
        q = self._delete_sql(name)
        args = {'pkey_val': pkey_val}
        
        return self._run_query(q, args, False)

    def upsert(self, name, data):
        q = self._upsert_sql(name, data)
            
        #   DATA contains only changed columns, upsert uses all table columns
        all_columns_data = {column_name: None for column_name in self.table_columns(name)}
        all_columns_data.update(data)

        return self._run_query(q, all_columns_data, False)

    def select(self, name, cond={}):
        q = self._select_sql(name, cond)
        return self._run_query(q, cond, True)

    #   SQL EXECUTION
    def _run_query(self, q, args, fetch_result):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(q, args)
        if fetch_result:
            data = cur.fetchall()
            return [dict(x) for x in data]
    
    #   SQL QUERIES CREATION
    def _delete_sql(self, name):
        pkey_name = self._pkeys[name]

        q = self._sql_template(name, 'delete')
        q = q.format(table_schema=sql.Identifier(self._schema), table_name=sql.Identifier(name), 
                     pkey_name=sql.Identifier(pkey_name))

        return q.as_string(self._conn)

    def _upsert_sql(self, name, data):
        table_columns = self.table_columns(name)

        #   all table columns
        all_columns = [sql.Identifier(column) for column in table_columns]
        all_columns_sql = sql.SQL(', ').join(all_columns)
        
        #   Columns to be updated
        updated_columns = [sql.Identifier(name) for name in data.keys()]
        updated_columns_sql = sql.SQL(', ').join(updated_columns)
        
        #   Pkey name
        pkey_name = self._pkeys[name]

        #   Values placeholders
        all_values = [sql.Placeholder(column) for column in table_columns]
        all_values_sql = sql.SQL(', ').join(all_values)

        q = self._sql_template(name, 'upsert')
        q = q.format(table_schema=sql.Identifier(self._schema), table_name=sql.Identifier(name),
                     pkey_name=sql.Identifier(pkey_name), all_columns=all_columns_sql,
                     updated_columns=updated_columns_sql, all_values=all_values_sql)
        
        return q.as_string(self._conn)

    def _select_sql(self, name, cond):
        select = self._select_all_sql(name)
        if cond:
            where = self._where_sql(name, cond)
            select = 'WITH a AS ({}) SELECT * FROM a'.format(select)
            select = ' '.join([select, where])
        return select

    def _select_all_sql(self, name):
        q = self._sql_template(name, 'select')
        q = q.format(table_schema=sql.Identifier(self._schema), table_name=sql.Identifier(name))

        return q.as_string(self._conn)

    def _where_sql(self, name, cond):
        columns = [sql.Identifier(name) for name in cond.keys()]
        values = [sql.Placeholder(name) for name in cond.keys()]
        
        q = self._sql_template(name, 'where')
        q = q.format(columns=sql.SQL(', ').join(columns), values=sql.SQL(', ').join(values))

        return q.as_string(self._conn)
    
    def _sql_template(self, resource_name, query_name):
        return sql.SQL(query_str[query_name])

    #   Additional methods
    def dump_table(self, table_name, column_name):
        q = query_str['dump_table']
        cur = self._conn.cursor()
        cur.execute(sql.SQL(q).format(
            sql.Identifier(self._schema),
            sql.Identifier(table_name),
            sql.Identifier(column_name)
        ))
        return cur.fetchall()

    def table_columns(self, table_name):
        if table_name not in self._table_columns_data:
            cur = self._conn.cursor()
            cur.execute(query_str['get_table_columns'], (self._schema, table_name))
            self._table_columns_data[table_name] = [x[0] for x in cur.fetchall()]
        return self._table_columns_data[table_name]
    
    def default_pkey_expr(self, table_name, column_name):
        if table_name not in self._default_pkey_expr:
            cur = self._conn.cursor()
            cur.execute(query_str['get_default_pkey_expr'], (self._schema, table_name, column_name))
            self._default_pkey_expr[table_name] = cur.fetchone()[0]
        return self._default_pkey_expr[table_name]


#   RAW SQL
query_str = {}

#   UPSERT/SELECT/DELETE
query_str['upsert'] = '''
--  NOTE: this works with postgresql9.6 and newer,
--  earlier versions were not tested
WITH
row_data AS (
    SELECT  (ROW({all_values})::{table_schema}.{table_name}).*
)
INSERT INTO {table_schema}.{table_name} ({updated_columns})
SELECT  {updated_columns}
FROM    row_data
ON CONFLICT ({pkey_name}) DO UPDATE
SET ({updated_columns}) = (SELECT {updated_columns} FROM (SELECT EXCLUDED.*) excl)
'''

query_str['delete'] = '''
DELETE  FROM {table_schema}.{table_name}
WHERE   {pkey_name} = %(pkey_val)s
'''

query_str['select'] = '''
SELECT  *
FROM    {table_schema}.{table_name}
'''

query_str['where'] = '''
WHERE   ({columns}) = ({values})
'''

#   ADDITIONAL SQL
query_str['dump_table'] = '''
SELECT  *
FROM    {}.{}
ORDER BY {}
'''
query_str['get_table_columns'] = '''
SELECT  column_name
FROM    information_schema.columns
WHERE   table_schema = %s
  AND   table_name   = %s
ORDER BY ordinal_position
'''
query_str['get_default_pkey_expr'] = '''
SELECT  column_default
FROM    information_schema.columns
WHERE   (table_schema, table_name, column_name) = (%s, %s, %s)
'''
