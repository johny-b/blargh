from blargh.engine import Engine
from blargh import exceptions

class Resource():
    model = None

    #   LOGIC
    def response(self, data, code, request_name, request_args, request_kwargs):
        '''
        Prepare response for request REQUEST_NAME with ARGS and KWARGS.

        Call to blargh.engine.Engine with given args and kwargs returned DATA and CODE.
        Here we implement all modifications required to turn "raw" Engine logic into
        final api, i.e.
            *   add headers
            *   move some information from data to headers

        Tuple (data, code, {}) is returned in basic version.
        '''
        return data, code, {}

    #   ROUTING TO ENGINE
    def get(self, *args, **kwargs):
        return self._call_engine('get', args, kwargs)

    def post(self, *args, **kwargs):
        return self._call_engine('post', args, kwargs)

    def put(self, *args, **kwargs):
        return self._call_engine('put', args, kwargs)

    def patch(self, *args, **kwargs):
        return self._call_engine('patch', args, kwargs)

    def delete(self, *args, **kwargs):
        return self._call_engine('delete', args, kwargs)
    
    def _call_engine(self, request_name, args, kwargs):
        '''
        REQUEST_NAME is get/post/patch/delete.put.

        This method:
            1.  Calls Engine.REQUEST_NAME(self.model.name, *args, **kwargs). 
                Such call has one of following results:
                *   returns some data and status
                *   raises any "known" exception (from zf.api.exceptions)
                *   raises any other exception
            2.  Captures all exceptions and changes them to data and status
            3.  Adds headers to the result
        '''
        engine_call = getattr(Engine, request_name)
        try:
            data, status = engine_call(self.model.name, *args, **kwargs)
        except exceptions.ClientError as e:
            # raise e
            #   this exception is an "expected" 4** status
            data, status = e.ext_data(), e.status
        except (exceptions.ServerError, exceptions.ProgrammingError) as e:
            #   this is strange and not expected, but still somehow predicted
            data, status = e.ext_data(), e.status
        except Exception as e:
            #   and this is totally unexpected, we assume this is 400
            #   TODO: this might be any internal error, i.e. we implicite assume 
            #         something will be not-None, it is None, so something crashes.
            #         Maybe such exceptions should be investigated?
            raise e
            bad_request = exceptions.e400()
            data, status = bad_request.ext_data(), bad_request.status
    
        return self.response(data, status, request_name, args, kwargs)
