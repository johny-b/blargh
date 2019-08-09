from flask import request
from flask_restful import Resource as FRResource, reqparse
from blargh.engine import Engine
import json

class Resource(FRResource):
    model = None
    
    def get(self, id_=None, auth=None):
        args = self._get_args()
        
        kwargs = {
            'auth': auth,
            'depth': args['depth'],
            'limit': args['limit'],
            'filter_': {},
        }

        if args['filter']:
            try:
                kwargs['filter_'] = json.loads(args['filter'])
            except json.decoder.JSONDecodeError:
                return {'msg': 'Filter is not a valid json'}, 400, {}

        if args['sort']:
            try:
                kwargs['sort'] = json.loads(args['sort'])
            except json.decoder.JSONDecodeError:
                return {'msg': 'sort is not a valid json'}, 400, {}
        
        data, status = Engine.get(self.model.name, id_, **kwargs)
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
        parser.add_argument('depth', type=int, default=1, location='args')
        parser.add_argument('filter', type=str, default='', location='args')
        parser.add_argument('limit', type=int, location='args')
        parser.add_argument('sort', type=str, location='args')
        return parser.parse_args(strict=False)
