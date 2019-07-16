from flask import request
from flask_restful import Resource as FRResource, reqparse
from blargh.engine import Engine
import json

class Resource(FRResource):
    model = None
    
    def get(self, id_=None, auth=None):
        args = self._get_args()

        #   Depth  - this is always set
        depth = args['depth']

        #   Search - this is optional
        filter_kwargs = {}
        if args['filter']:
            try:
                filter_kwargs = json.loads(args['filter'])
            except json.decoder.JSONDecodeError:
                return {'msg': 'Filter is not a valid json'}, 400, {}
        
        data, status = Engine.get(self.model.name, id_, filter_kwargs, depth=depth, auth=auth)
        return data, status, {}
    
    def delete(self, id_, auth=None):
        data, status = Engine.delete(self.model.name, id_, auth=auth)
        return data, status, {}

    def post(self, auth=None):
        data, status = Engine.post(self.model.name, request.get_json(), auth=auth)
        return data, status, {}
    
    def put(self, id_, auth=None):
        data, status = Engine.put(self.model.name, id_, request.get_json(), auth=auth)
        return data, status, {}
    
    def patch(self, id_, auth=None):
        data, status = Engine.patch(self.model.name, id_, request.get_json(), auth=auth)
        return data, status, {}

    def _get_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('depth', type=int, default=1)
        parser.add_argument('filter', type=str, default='')
        return parser.parse_args(strict=False)
