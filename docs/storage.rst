Storage
=======

Storage is a place where all the data is stored (not a surprise).

There are currently three built-in Storages classes, but since possible places where 
one could store REST API data are infinite, there is also a pretty straightforward
method of creating additional Storages.


DictStorage
-----------

All the data is in a python dictionary. Data is stored in a dictionary. 
Useful for prototyping, testing and deploying one-time applications.

.. code-block:: python

    data = {}
    storage = engine.DictStorage(data)

initial data doesn't have to be empty:

.. code-block:: python

    data = {
        'cookie': {1: {'id': 1, 'type': 'muffin'}, 
                   2: {'id': 2, 'type': 'shortbread', 'jar': 1}}, 
        'jar': {1: {'id': 1, 'cookies': [2]}}
    }
    storage = engine.DictStorage(data)





PickledDictStorage
------------------

The same as DictStorage, but dictionary is read from a pickle file and saved there after every change.
This should not be considered in any way a "production" quality storage - it's just an extension
of DictStorage that allows restarts without loosing data.

.. code-block:: python

    file_with_pickled_dictionary = 'data.pickle'
    storage = engine.PickledDictStorage(data)

PGStorage
---------

The only serious storage.
Data is stored in a single schema in a PostgreSQL Database.

.. code-block:: python

    import psycopg2

    connstr = ''
    schema_name = 'cookies'

    def storage():
        conn = psycopg2.connect(connstr)
        return engine.PGStorage(conn, schema_name)

[TODO - why function?]

PGStorage behaviour can be modified/extended in many ways, few examples are in the cookbook:

- `Read-only resources <cookbook.html#read-only-resources>`__
- `Resource access restriction <cookbook.html#resource-access-restriction>`__

Creating your own storage
-------------------------

Each storage should extend abstract class :code:`blargh.engine.storage.BaseStorage`,
implementing all of its required functions.

.. autoclass:: blargh.engine.storage.BaseStorage
    :members:
