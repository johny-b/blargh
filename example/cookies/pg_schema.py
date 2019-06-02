pg_schema_sql = '''
CREATE TABLE jar (
    id      serial PRIMARY KEY
);

CREATE TABLE cookie (
    id      serial PRIMARY KEY,
    jar     integer REFERENCES jar(id) DEFERRABLE,
    type    text
);
'''
