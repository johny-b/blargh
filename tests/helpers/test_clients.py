from urllib.parse import urlunparse, urlencode
import json

from flask import Flask
from blargh.api import basic, flask

from flask_jwt_extended import create_access_token, JWTManager, get_jwt_identity, jwt_required
 
class AuthClient():
    def __init__(self):
        self._auth_data = {}

    def login(self, data):
        self._auth_data = data

    def logout(self):
        self._auth_data = {}

class BaseApiClient():
    def __getattr__(self, name):
        if name in 'get post patch put delete'.split(' '):
            return getattr(basic, name)

class BaseApiClientAuth(AuthClient):
    def get(self, *args, **kwargs):
        return basic.get(*args, **kwargs, auth=self._auth_data.copy())

    def post(self, *args, **kwargs):
        return basic.post(*args, **kwargs, auth=self._auth_data.copy())

    def put(self, *args, **kwargs):
        return basic.put(*args, **kwargs, auth=self._auth_data.copy())

    def patch(self, *args, **kwargs):
        return basic.patch(*args, **kwargs, auth=self._auth_data.copy())

    def delete(self, *args, **kwargs):
        return basic.delete(*args, **kwargs, auth=self._auth_data.copy())

class FlaskClient(BaseApiClient):
    '''
    Flask client
        *   on initialization starts Flask application, adds blargh.flask_glue.Api
            and creates defaults resources
        *   on get/post/patch/delete/put:
            *   creates appropriate URL
            *   requests this URL from creted flask app
            *   returns response data and status
    '''
    def __init__(self):
        self._app = Flask(__name__)
        self._app.config['TESTING'] = True
        self._flask_client = self._app.test_client()
        self._api = flask.Api(self._app)
        self._api.add_default_blargh_resources('/api')

    def get(self, resource, id_=None, filter_=None, depth=None):
        url_parts = ['' for x in range(6)]

        #   Name & id
        if id_:
            url_parts[2] = '/api/{}/{}'.format(resource, id_)
        else:
            url_parts[2] = '/api/{}'.format(resource)
        
        params = {}
        if depth is not None:
            params['depth'] = depth
        if filter_ is not None:
            params['filter'] = json.dumps(filter_)
        
        url_parts[4] = urlencode(params)
        url = urlunparse(url_parts)
        
        return self._make_call('get', url, {})

    def delete(self, resource, id_):
        url = '/api/{}/{}'.format(resource, id_)
        return self._make_call('delete', url, {})

    def post(self, resource, data):
        url = '/api/{}'.format(resource)
        return self._make_call('post', url, dict(data=json.dumps(data), content_type='application/json'))

    def put(self, resource, id_, data):
        url = '/api/{}/{}'.format(resource, id_)
        return self._make_call('put', url, dict(data=json.dumps(data), content_type='application/json'))

    def patch(self, resource, id_, data):
        url = '/api/{}/{}'.format(resource, id_)
        return self._make_call('patch', url, dict(data=json.dumps(data), content_type='application/json'))

    def _make_call(self, method, url, kwargs):
        res = getattr(self._flask_client, method)(url, **kwargs)
        return self._res_2_data_status_headers(res)

    def _res_2_data_status_headers(self, res):
        data = json.loads(res.get_data().decode('utf8'))
        status = int(res.status.split(' ')[0])
        headers = res.headers

        return data, status, headers


class FlaskClientAuth(FlaskClient, AuthClient):
    def __init__(self):
        '''
        Note: things are initialized in not intuitive order, but this is 
        required because of some unusual things done in _init_flask_jwt.

        Maybe replacing add_default_blargh_resources with some custom function would be better.
        '''
        super(AuthClient).__init__()

        #   1.  Init restful api
        self._api = flask.Api()
        self._api.add_default_blargh_resources('/api')
        
        #   2.  Create flask app
        self._app = Flask(__name__)
        
        #   3.  Init all JWT-related stuff
        #       (Note: this alters not only client, but also api)
        self._init_flask_jwt()
        
        #   4.  Connect api and app
        self._api.init_app(self._app)
        
        #   5.  Set testing
        self._app.config['TESTING'] = True
        self._flask_client = self._app.test_client()
    
    def _make_call(self, method, url, kwargs):
        '''
        Add authorization header
        '''
        with self._app.test_request_context():
            token = create_access_token(identity=self._auth_data)

        headers = kwargs.get('headers', {})
        headers['Authorization'] = 'Bearer ' + token
        kwargs['headers'] = headers

        return super()._make_call(method, url, kwargs)
    
    def _init_flask_jwt(self):
        '''
        PURPOSE: All resources should require authentication
        METHOD:  Uses flask-restful decorator jwt_required. Decorator is added to
                 each resources' method_decorators (more precise: new resource with 
                 this decorator is created, this is caused by flask-restful internals).
        '''
        def jwt_auth(f):
            '''
            decorated function gets auth=get_jwt_identity()
            '''
            @jwt_required
            def wrapped(*args, **kwargs):
                auth = get_jwt_identity()
                if auth:
                    kwargs['auth'] = auth
                return f(*args, **kwargs)
            return wrapped
    
        #   "Standard" server-side JWT initialization
        self._app.config['JWT_SECRET_KEY'] = '123soverysecret'
        JWTManager(self._app)
    
        #   Current state: resource classes are blargh.api.resource.FlaskRestfulResources, 
        #                  and they know nothing about JWT
        #   Desired state: resource classes have .method_decorators including jwt_auth (above)
        #   Method: "simple" appending to .method_decorators works well for single test,
        #           but this would require cleanup/reloading after each test (since FlaskRestfulResource was modified). 
        #           Instead, resource classes are substituted with new classes inheriting from old ones.
        new_resources = []
        
        #   Note: this is not documented flask-restful.Api stuff
        for old_row in self._api.resources:
            old_cls, *rest = old_row
            new_cls = type(old_cls.__name__, 
                           (old_cls,), 
                           {'method_decorators': old_cls.method_decorators + [jwt_auth]})
            new_row = [new_cls] + rest
            new_resources.append(new_row)
    
        self._api.resources = new_resources
