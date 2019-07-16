from blargh.engine import Engine
from blargh import exceptions

def _call_engine(request_name, resource_name, args, kwargs):
    '''
    Executes REQUEST_NAME call on resource RESOURCE_NAME with ARGS and KWARGS.
    Captures all blargh exceptions and returns their data/status. Other exceptions are propagated.

    Also adds "headers" - an empty dictionary - to maintain the same interface as
    in flask-restful API.
    '''
    engine_call = getattr(Engine, request_name)

    try:
        data, status = engine_call(resource_name, *args, **kwargs)
    except exceptions.Error as e:
        data, status = e.ext_data(), e.status

    return data, status, {}

def get(name, *args, **kwargs):
    return _call_engine('get', name, args, kwargs)

def post(name, *args, **kwargs):
    return _call_engine('post', name, args, kwargs)

def put(name, *args, **kwargs):
    return _call_engine('put', name, args, kwargs)

def patch(name, *args, **kwargs):
    return _call_engine('patch', name, args, kwargs)

def delete(name, *args, **kwargs):
    return _call_engine('delete', name, args, kwargs)
