pg_schema_sql = '''
CREATE TABLE male(
    id      serial PRIMARY KEY,
    name    text
);

CREATE TABLE female(
    id      serial PRIMARY KEY,
    name    text,
    husband integer UNIQUE DEFERRABLE REFERENCES male(id) DEFERRABLE
);

CREATE TABLE child(
    id      serial PRIMARY KEY,
    name    text,
    father  integer REFERENCES male(id)   DEFERRABLE,
    mother  integer REFERENCES female(id) DEFERRABLE
);
'''
