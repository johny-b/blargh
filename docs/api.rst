API
===

Request structure
-----------------

Allowed requests
^^^^^^^^^^^^^^^^
**Blargh** currently implements following requests:

.. code-block:: python
    
    from blargh.api.basic import get, post, put, patch, get
    
    data = {'foo': 'bar'}
    name = 'cookies'
    id_ = 1
    
    get(name, depth=1, filter_={})
    get(name, id_, depth=1)
    post(name, data)
    put(name, id_, data)
    patch(name, id_, data)
    detele(name, id_)

Other possible requests (PATCH/DELETE on a collection, OPTIONS, HEAD etc) have to be implemented
separately, e.g. like this: `Patch on a collection <cookbook.html#patch-on-a-collection>`__.

GET args
^^^^^^^^

Besides resource name and optional id, ``get()`` accepts also:

:depth: Non-negative integer, default 1, controlling relational fields behaviour. Related objects will be displayed
        with value ``depth = depth - 1``, recursively, and ``depth = 0`` returns only id. Example:

        >>> for depth in range(0, 4):
        ...    pprint(get('cookie', 1, depth=depth)[0])
        ...
        1
        {'id': 1, 'jar': 1, 'type': 'biscuit'}
        {'id': 1, 'jar': {'cookies': [1, 2], 'id': 1}, 'type': 'biscuit'}
        {'id': 1,
         'jar': {'cookies': [{'id': 1, 'jar': 1, 'type': 'biscuit'},
                             {'id': 2, 'jar': 1, 'type': 'muffin'}],
                 'id': 1},
         'type': 'biscuit'}

        **Note:** depth is by default not limited, and calls with ``depth = 10`` can easly eat up all your RAM.
        It is strongly advised to force some limit in the final application.

:filter\_: Dictionary that will be a subset of each returned dictionary. Example again:
 
          >>> pprint(get('cookie')[0])
          [{'id': 1, 'jar': 1, 'type': 'biscuit'},
           {'id': 2, 'jar': 1, 'type': 'muffin'},
           {'id': 3, 'jar': 2, 'type': 'shortbread'}]
          >>> pprint(get('cookie', filter_={'jar': 1})[0])
          [{'id': 1, 'jar': 1, 'type': 'biscuit'}, 
           {'id': 2, 'jar': 1, 'type': 'muffin'}]
          >>> pprint(get('cookie', filter_={'jar': 1, 'type': 'biscuit'})[0])
          [{'id': 1, 'jar': 1, 'type': 'biscuit'}]
          >>> pprint(get('cookie', filter_={'type': 'shortbread'})[0])
          [{'id': 3, 'jar': 2, 'type': 'shortbread'}]
          >>> pprint(get('cookie', filter_={'type': 'gingerbread'})[0])
          []


Other arguments (pagination, field selection, more advanced search etc.) will probably be added in the future.

POST/PATCH/PUT data
^^^^^^^^^^^^^^^^^^^

``patch()``/``put()`` data is a dictionary, ``post()`` data is either a dictionary or a list of dictionaries. List of dictionaries is treated
the same way as set of subsequent ``post()`` calls, that either all succeed or all fail. Dictionary keys are fields external names, values - 
anything that given field can parse. For standard field types:

Scalar
    Anything, if fields ``type_ is None``, or anything that can be reversibly casted to ``type_`` if ``type_ is not None``.

Calc
    If field has defined ``setter``  - any value accepted by the ``setter`` function (i.e. any value that passed to ``setter`` doesn't 
    raise an exception). If ``setter is None``, nothing is allowed.

Rel
    Id or a dictionary if not ``field.multi``, or list of those otherwise.
    Id has to be a valid id of an object stored in this field, dictionary will be used as POST data.

    For example, let's assume we want to create a new jar with a new cookie. We can do this in two separate requests:

    .. code-block:: python

        post('cookie', {'type': 'gingerbread'})
        #   Let's assume POSTed cookie has id 4
        post('jar', {'cookies': [4]})

    but also in one request, either posting a jar:

    .. code-block:: python

        post('jar', {'cookies': [{'type': 'gingerbread'}]})

    or a cookie:
    
    .. code-block:: python

        post('cookie', {'type': 'gingerbread', 'jar': {}})
    
Check `Data model fields <data_model.html#fields>`__ for more information.

Vague requests
^^^^^^^^^^^^^^

It is possible to make a call with more-or-less conflicting data, for example (assuming ``example.cookies.dm`` is used):
 
>>> patch('jar', 1, {'cookies': [{'jar': 2, 'type': 'gingerbread'}]})

Here we patch a jar, setting its cookies to include a new cookie (thus creating it), but this new cookie
already is set to be in another jar. The result is cookie in jar 1, so ``'jar': 2`` is just ignored.

This could get worse with bit more complicated datamodel (``example.family.dm``):
    
>>> print(get('female', 2)[0].get('husband'))
2
>>> patch('female', 1, {'husband': {'wife': 2}})[0]
{'id': 1, 'name': 'f1', 'husband': 3, 'children': [1], 'url': 'female/1'}
>>> print(get('female', 2)[0].get('husband'))
None

New male is created with ``wife = 2``, so male 2 (previous husband of female 2) gets divorced first, and later this new male's wife is set to be female 1.
This is equivalent to:

.. code-block:: python
    
    # creates male with ID 3 and set's it as new husband of female 2
    post('male', {'wife': 2})           
    # sets male 3 as husband of female 1 - so female 2 becomes single
    patch('female', 1, {'husband': 3})  

Such requests are currently allowed, but **this will probably change in future** and they will return 422.


API layers
----------

Api has few nested layers, user should choose the one most appropriate.

blargh.engine.Engine
^^^^^^^^^^^^^^^^^^^^

Deepest layer. All requests that would result in status other than 2** end in `exceptions <data_model.html>`__.
Useful for debugging, or when we want to deal with "incorrect" request in some special way.

.. code-block:: python

    # ... (data model, storage, engine.setup())
    from blargh.engine import Engine
    
    # returns ({'id': 7, 'type': 'shortbread'}, 201)
    Engine.put('cookie', 7, {'type': 'shortbread'})  
    
    # raises blargh.exceptions.client.e404
    Engine.delete('cookie', 8)                       

blargh.api.resource.Resource
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Blargh customiation could be done in various ways. The cleanest way is to create one class for every resource
and modify this class methods, and :code:`blargh.api.resource.Resource` should be the base class.

Resource methods differ from Engine in two ways:
    
- All blargh exceptions are caught and their data/code are returned.
  Other exceptions are reraised, though this might change in the future and some generic 500 will be returned.
- Returned tuple contains also headers (an empty dictionary, in the base class).

.. code-block:: python
    
    # ... (data model, storage, engine.setup())
    from blargh.api.resource import Resource
    
    class cookie(Resource):
        model = dm.object('cookie')

        def post(self, in_data):
            out_data, code, headers = super().post(in_data)

            #   add Location header if resource was created
            if code == 201:
                headers['Location'] = 'cookie/{}'.format(out_data['id'])
            return out_data, code, headers
            

        def delete(self, id_):
            return "NOPE, COOKIES ARE FOREVER", 400, {}
    
    # returns ({'id': 7, 'type': 'shortbread'}, 201, {})
    cookie().put(7, {'type': 'shortbread'})  

    # returns ('NOPE, COOKIES ARE FOREVER', 400, {})
    cookie().delete(8)                       
    
    # returns ({'id': 8, 'type': 'muffin'}, 201, {'Location': 'cookie/8'})
    cookie().post({'type': 'muffin'})

basic
^^^^^

The same behaviour as :code:`blargh.api.resource.Resource`, but all Resource classes are 
created in a implicit way. Provides simple function-only interface.

.. code-block:: python
    
    # ... (data model, storage, engine.setup())
    from blargh.api.basic import put, delete

    # returns ({'id': 7, 'type': 'shortbread'}, 201, {})
    put('cookie', {'type': 'shortbread'})
    
    # returns ({'error': {'code': 'OBJECT_DOES_NOT_EXIST', 
    #                     'details': {'object_name': 'cookie', 
    #                      'object_id': 8}}}, 
    #          404, {})
    delete('cookie', 8)

Integration with Flask
----------------------

Flask + REST = `Flask-RESTful <https://flask-restful.readthedocs.io/en/latest>`_.

When you replace two Flask-RESTful classes with their blargh counterparts:

- :code:`flask_restful.Resource` -> :code:`blargh.api.resource.FlaskRestfulResource` 
- :code:`flask_restful.Api` -> :code:`blargh.api.flask.Api`.

you should be able to use all Flask-RESTful features together with blargh.

So, complete Flask + Flask-RESTful + blargh application code is a compilation of
`Flask-RESTful minimal api <https://flask-restful.readthedocs.io/en/latest/quickstart.html#a-minimal-api>`__
and `Blargh basic usage <quickstart.html#basic-usage>`__:

.. code-block:: python

    from flask import Flask
    
    #   this replaces `from flask_restful import Resource, Api`
    from blargh.api.flask import Api
    from blargh.api.resource import FlaskRestfulResource as Resource

    #   blargh initialization
    from blargh import engine
    from example.cookies import dm
    storage = engine.DictStorage({})
    engine.setup(dm, storage)
        
    #   this does not change
    app = Flask(__name__)
    api = Api(app)
    
    #   blargish classes
    class Cookie(Resource):
        model = dm.object('cookie')

    class Jar(Resource):
        model = dm.object('jar')
    
    #   blargish api has the same interface as Flask-RESTful api
    api.add_resource(Cookie, '/cookie')
    api.add_resource(Jar, '/jar')
    
    if __name__ == '__main__':
        app.run(debug=True)

After saving this in :code:`app.py` and starting debug server with :code:`python3 app.py` 
our cookie managment system is ready:

.. code-block:: bash

    $ curl -d '{"type":"shortbread"}' -H "Content-Type: application/json" \ 
           -X POST http://0.0.0.0:5000/cookie
    {
        "id": 1,
        "type": "shortbread"
    }
    $ curl -d '{"type":"muffin"}' -H "Content-Type: application/json" \
           -X POST http://0.0.0.0:5000/cookie
    {
        "id": 2,
        "type": "muffin"
    }
    $ curl -d '{"cookies":[1,2]}' -H "Content-Type: application/json" \
           -X POST http://0.0.0.0:5000/jar
    {
        "id": 1,
        "cookies": [
            1,
            2
        ]
    }
    $ curl -X GET http://0.0.0.0:5000/jar?depth=2
    [
        {
            "id": 1,
            "cookies": [
                {
                    "id": 1,
                    "type": "shortbread",
                    "jar": 1
                },
                {
                    "id": 2,
                    "type": "muffin",
                    "jar": 1
                }
            ]
        }
    ]
    
