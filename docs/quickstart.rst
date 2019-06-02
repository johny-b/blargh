
Quickstart
==========

About blargh
----------

Two main concepts behind **blargh**:

* Any RESTful service is a `CRUD <https://pl.wikipedia.org/wiki/CRUD>`_ application, that can be divided into three layers:
  
  * Database
  * Engine, usually some sort of `ORM <https://en.wikipedia.org/wiki/Object-relational_mapping>`_
  * Web application

  In **blargh** those layers are independent, and the Engine core allows connecting different storages/web applications.
  In particular, middle layer can be used as a REST-like database interface.

* Main part of any RESTful service is defined by its data model - set of resources and relationships between them.
  Everything else is details, and **blargh** doesn't deal with those (but provides tools to implement them).

So, creating a RESTful service with **blargh** consists of three steps:

1. Define the data model, in a **blarghish** language
2. Select storage
3. Connect the outer layer (eg. :doc:`Flask-Restful <flask_restful:index>`)


Basic usage
-----------

Initialization:

.. code-block:: python
    
    from blargh import engine
    from blargh.api.basic import post, get, patch  # , put, delete
    
    #   First, we need to declare the data model. Here we import data model with
    #   two objects: cookies and jars. Cookie has a defined type and might be in a jar.
    from example.cookies import dm
    
    #   we may store our data in various places, e.g. in a dictionary ...
    data = {}
    
    #   ... as long as we provide proper interface
    storage = engine.DictStorage(data)
    
    #   final preparation step
    engine.setup(dm, storage)
    
And now, let's make some cookies. 
Note: each call returns tuple :code:`(data, status, headers)` - here only the first element is shown.

>>> post('cookie', {'type': 'shortbread'})[0]
{'id': 1, 'type': 'shortbread'}
>>> post('cookie', {'type': 'muffin'})[0]
{'id': 2, 'type': 'muffin'}
>>> post('jar', {}))[0]
{'id': 1, 'cookies': []}

We can put our cookies in a jar and check our current state

>>> patch('jar', 1, {'cookies': [1, 2]})[0]
{'id': 1, 'cookies': [1, 2]}
>>> get('cookie')[0]
[{'id': 1, 'type': 'shortbread', 'jar': 1}, {'id': 2, 'type': 'muffin', 'jar': 1}]

And this is how it looks internally, when using DictStorage

>>> from pprint import pprint
>>> pprint(data)
{'cookie': {1: {'id': 1, 'jar': 1, 'type': 'shortbread'},
            2: {'id': 2, 'jar': 1, 'type': 'muffin'}},
 'jar': {1: {'cookies': [1, 2], 'id': 1}}}

Getting started
---------------

Setting up a **blargh**-based application is clearly divided into three steps.
We have to define data model, select storage, and decide which api class will be used.

Each of those three parts has detailed chapter further in the docs, here the main concept is described.
    


Data model
^^^^^^^^^^

Data model describes objects and relationships between them.
Here's generously commented data model that we used in :doc:`/basic_usage`:

.. literalinclude:: ../example/cookies/data_model.py
   :caption: example/cookies/data_model.py

Some general remarks:

* example above presents most of **blargh** data model
* **blargh** core contains three types of fields: Scalar, Rel and Calc, but 
  extending them/creating own fields is simple and strongly encourged.
  Any arbitrary behaviour can be achived this way.
* data model *should* be declared before application starts and *should not* be changed
  later, but runtime modifications work well, though rather by accident than by design

Detailed data modeling manual: :doc:`/data_model`

Storage
^^^^^^^

There are currently three storage classes:

:code:`blargh.engine.storage.DictStorage(data_dict)`
    Data is stored in a dictionary. Useful for prototyping, testing and deploying one-time applications.

:code:`blargh.engine.storage.PickledDictStorage(file_name)`
    The same as DictStorage, but dictionary is read from a pickle file and saved there after every change.
    This should not be considered in any way a "production" quality storage.
    
:code:`blargh.engine.storage.PGStorage(conn, schema, query_cls=Query)`
    Data is stored in a PostgreSQL database. This is the only "serious" storage.

Extending **blargh** by creating custom Storage classes should be pretty simple.

Further reading: :doc:`/storage`

API
^^^

There are currently two api classes:

:code:`blargh.api.basic`
    Pure python api, demonstrated in :doc:`/basic_usage`. Useful as a base for any other
    final application build over it: the "REST API" thing is here, all you need is to connect
    it to the top layer.

:code:`blargh.api.flask`
    **blargh** connected with :doc:`Flask-Restful <sphinx:quickstart>`.
    Everything in Flask-Restful should more-or-less work, but instead of implementing all
    methods for all objects, you simply need to define a data model for all resources.

For debugging and development :code:`engine.Engine` - layer just under api - can be useful.
They behave exactly the same for requests ending with 2** status:

>>> basic.get('cookie', 1)
({'id': 1, 'type': 'Shortbread'}, 200, {})
>>> engine.Engine.get('cookie', 1)
({'id': 1, 'type': 'Shortbread'}, 200)

but in :code:`engine.Engine` higher codes are raised as exceptions:

>>> basic.get('cookie', 7)
({'error': {'code': 'OBJECT_DOES_NOT_EXIST', 'details': {'object_name': 'cookie', 'object_id': 7}}}, 404, {})
>>> engine.Engine.get('cookie', 7)
Traceback (most recent call last):
(...)
blargh.exceptions.client.e404: object_does_not_exist (404)
{'object_name': 'cookie', 'object_id': 7}

Full example
------------

Here's the code:

.. literalinclude:: ../example/cookies/flask_app.py
   :caption: example/cookies/flask_app.py

This is how we start our cookie managment app::

    $ python3 example/cookies/flask_app.py

And this is how we create a cookie, a jar, and how we put one in the other::

    $ curl localhost:5000/cookie -X POST -d '{"type":"shortbread"}' -H "Content-Type: application/json"
    {
        "id": 1,
        "type": "shortbread"
    }
    $ curl localhost:5000/jar -X POST -d '{}' -H "Content-Type: application/json"
    {
        "id": 1,
        "cookies": []
    }
    $ curl localhost:5000/cookie/1 -X PATCH -d '{"jar": 1}' -H "Content-Type: application/json"
    {
        "id": 1,
        "type": "shortbread",
        "jar": 1
    }

Now, if you need:

    *   different data model than our favourite (cookie, jar) pair - replace ``from example.cookies import dm``
        with your data model code [TODO - link data_model]
    *   other storage (maybe more permanent than in-memory dictionary?) - replace ``engine.DictStorage({})``
        with either a build-in storage, or create own storage [TODO - link storage]
    *   other endpoint(s) than default "cookie name = endpoint name" - replace ``blargh.add_default_blargh_resources('/')``
        with :doc:`Flask-Restful <flask_restful:quickstart>` endpoints, as shown in [TODO - link endpoints]
    *   other web server than flask - replace ``flask`` with ``basic`` in ``from blargh.api import flask`` and connect them on you own


