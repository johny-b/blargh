from .resource import FlaskRestfulResource

from flask_restful import Api as FRApi
from blargh.engine import dm
from os import path

class Api(FRApi):
    def add_resource(self, resource, *urls, **kwargs):
        super().add_resource(resource, *urls, **kwargs)
        
        #   TODO
        #   This is extremaly ugly - just a POC
        def get_url(instance):
            import re
            from flask import request
            url = request.url_root[:-1] + urls[0]
            url = re.sub('<.+$', '', url)
            url = path.join(url, str(instance.id()))
            return url
        
        #   Operation performed only for FlaskRestfulResources.
        #   Simple flask_restful.Resource is also accepted here.
        if issubclass(resource, FlaskRestfulResource):
            obj_name = resource.model.name
            url_field = dm().object(obj_name).field('url')
            if url_field is not None:
                url_field._getter = get_url

    def add_default_blargh_resources(self, base):
        for name, model in dm().objects().items():
            #   Create class inheriting from Resource, with model
            cls = type(name, (FlaskRestfulResource,), {'model': model})

            #   Resource URIs - collection and single element
            collection_url = path.join(base, name)
            object_url = path.join(collection_url, '<id_>')
            
            #   Add resource
            self.add_resource(cls, object_url, collection_url)
