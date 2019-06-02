from ..engine import dm
from .resource import Resource

#   Each named resource has separate class, with Resource as its base class.
#   Here are stored single resource classes
_resource_cls = {}

def resource(name):
    if name not in _resource_cls:
        model = dm().object(name)
        cls = type(name, (Resource,), {'model': model})
        _resource_cls[name] = cls
    return _resource_cls[name]()

def get(name, *args, **kwargs):
    return resource(name).get(*args, **kwargs)

def post(name, *args, **kwargs):
    return resource(name).post(*args, **kwargs)

def put(name, *args, **kwargs):
    return resource(name).put(*args, **kwargs)

def patch(name, *args, **kwargs):
    return resource(name).patch(*args, **kwargs)

def delete(name, *args, **kwargs):
    return resource(name).delete(*args, **kwargs)
