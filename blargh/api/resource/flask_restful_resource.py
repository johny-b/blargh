from .resource import Resource
from flask import request
from flask_restful import Resource as FRResource, reqparse
import json

class FlaskRestfulResource(FRResource, Resource):
    model = None
    
    ###########
    #   GET   #
    ###########
    def get(self, id_=None, auth=None):
        #   Resource name, request args
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
        
        return super().get(id_, filter_kwargs, depth=depth, auth=auth)
    
    def _get_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('depth', type=int, default=1)
        parser.add_argument('filter', type=str, default='')
        return parser.parse_args(strict=False)

    ##############
    #   OTHER    #
    ##############
    def delete(self, id_=None, auth=None):
        if id_ is None:
            return {'msg': 'DELETE requires resource ID'}, 400, {}
        return super().delete(id_, auth=auth)

    def post(self, id_=None, auth=None):
        if id_ is not None:
            return {'msg': 'POST is allowed only on collection, got id {}'.format(id_)}, 400, {}
        return super().post(request.get_json(), auth=auth)
    
    def put(self, id_=None, auth=None):
        if id_ is None:
            return {'msg': 'PUT requires resource ID'}, 400, {}
        return super().put(id_, request.get_json(), auth=auth)
    
    def patch(self, id_=None, auth=None):
        if id_ is None:
            return {'msg': 'PATCH requires resource ID'}, 400, {}
        return super().patch(id_, request.get_json(), auth=auth)
