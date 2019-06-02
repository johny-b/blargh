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

Other possible requests (PATCH/DELETE on a collection, OPTIONS, HEAD etc) have to be implemented if needed.
Sample implementation of PATCH on a collection can be found in the [TODO - link] cookbook.

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


Other arguments will be probably added in future, if needed.

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
    
Check [TODO - link] data_model_fields for more information.

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

Such requests are allowed only because I was too lazy to implement detecting them, but **this should change in future**.



API classes
-----------

basic
^^^^^

flask
^^^^^

Engine class
^^^^^^^^^^^^

Resource class
^^^^^^^^^^^^^^



