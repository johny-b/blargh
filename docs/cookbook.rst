Cookbook
========

Authentication
--------------

Simple authentication - each user has access only to resources created by her.

.. code-block:: python

    from blargh import engine
    from example.cookies import dm
    
    #   1.  Information about resource owner has to be stored somewhere,
    #       e.g. as a hidden field - so we add user_id field.
    from blargh.data_model.fields import Scalar
    dm.object('cookie').add_field(Scalar('user_id', hidden=True, type_=int))
    dm.object('jar').add_field(Scalar('user_id', hidden=True, type_=int))
    
    #   2.  Create a custom storage (e.g. extending DictStorage)
    from blargh.exceptions import e400, e401, e404
    class AuthDictStorage(engine.DictStorage):
        '''Dict storage with authentication.
    
        All resources must have user_id field. This field should never be set
        by user in an explicit way, so should stay hidden (or readonly).
    
        This user_id:
            *   is added to saved data in _write_repr
            *   is checked in load()
            *   is added to filter data in selected_ids()
            *   is available via _current_user_id() method
    
        Note: public methods are documented in engine.DictStorage - 
        interface & operation stay the same.
        '''
        def load(self, name, id_):
            user_id = self._current_user_id()
            instance_data = super().load(name, id_)
            if instance_data['user_id'] != user_id:
                raise e404('resource does not exist, at least for you, hehehe')
            return instance_data
    
        def selected_ids(self, name, data):
            user_id = self._current_user_id()
            data['user_id'] = user_id
            return super().selected_ids(name, data)
    
        def _write_repr(self, instance):
            user_id = self._current_user_id()
            instance_data = super()._write_repr(instance)
            instance_data['user_id'] = user_id
            return instance_data
    
        def _current_user_id(self):
            '''Return current authenticated user's ID'''
            auth_data = engine.world().get_auth()
            if not auth_data:
                raise e401('authentication is required')
            elif 'user_id' not in auth_data:
                raise e400('user_id missing in authentication data')
            user_id = auth_data['user_id']
            return user_id
    
    
    #   3. TEST
    storage = AuthDictStorage({})
    engine.setup(dm, storage)
    from blargh.api.basic import put, get
    
    #   Attempt to create a cookie without authentication
    assert put('cookie', 1, {'type': 'muffin'}) == \
        ({'error': {'code': 'UNAUTHORIZED', 'details': {'msg': 'authentication is required'}}}, 401, {})
    
    #   Authenticated cookie creation
    assert put('cookie', 1, {'type': 'muffin'}, auth={'user_id': 1}) == \
        ({'id': 1, 'type': 'muffin'}, 201, {})
    
    #   Single cookie access, by cookie creator and by other user
    assert get('cookie', 1, auth={'user_id': 1}) == ({'id': 1, 'type': 'muffin'}, 200, {})
    assert get('cookie', 1, auth={'user_id': 2}) == \
        ({'error': {'code': 'OBJECT_DOES_NOT_EXIST', 
                    'details': {'msg': 'resource does not exist, at least for you, hehehe'}}}, 
         404, {})
    
    #   Cookie collection access, by cookie creator and by other user
    assert get('cookie', auth={'user_id': 1}) == ([{'id': 1, 'type': 'muffin'}], 200, {})
    assert get('cookie', auth={'user_id': 2}) == ([], 200, {})
    
    #   Attempt to in-direct cookie modification
    assert put('jar', 1, {'cookies': [1]}, auth={'user_id': 1}) == ({'id': 1, 'cookies': [1]}, 201, {})
    assert put('jar', 1, {'cookies': [1]}, auth={'user_id': 2}) == \
        ({'error': {'code': 'OBJECT_DOES_NOT_EXIST', 
                    'details': {'msg': 'resource does not exist, at least for you, hehehe'}}}, 
         404, {})

If one uses `Resource base class <api.html#blargh-api-resource-resource>`__, something like this should do the job:

.. code-block:: python

    from blargh.api.resource import Resource
    
    def get_auth_data():
        return {'user_id': 42}

    def add_auth_data(f):
        def authenticated_call(*args, **kwargs):
            return f(*args, **kwargs, auth=get_auth_data())
        return authenticated_call

    class AuthResource(Resource):
        post = add_auth_data(Resource.post)
        put = add_auth_data(Resource.put)
        get = add_auth_data(Resource.get)
        patch = add_auth_data(Resource.patch)
        delete = add_auth_data(Resource.delete)
    
    #   And AuthResource is our new base class
    class Cookie(AuthResource):
        model = dm.object('cookie')



Custom Field class 1
--------------------

[TODO]

Custom Field class 2
--------------------

[TODO]

Read Only Resources
-------------------

[TODO]

Resource access restriction
---------------------------

[TODO]

PATCH on a collection
---------------------

[TODO]
