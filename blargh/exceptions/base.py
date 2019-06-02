class Error(Exception):
    '''Exception that is the base class for all **blargh** error exceptions
    '''
    status = 500
    code = 'unknown_error'
    def __init__(self, *args, **kwargs):
        if args:
            msg_str = ';'.join([str(x) for x in args])
            if 'msg' not in kwargs:
                kwargs['msg'] = msg_str
            else:
                kwargs['_additional_msg'] = msg_str
        self.details = kwargs
    
    def __str__(self):
        return '{} ({})\n{}'.format(self.code, self.status, str(self.details))
    
    def ext_data(self):
        return {'error': {'code': self.code.upper(), 'details': self.details}}


class ClientError(Error):
    '''Exception indicating end-user error. Our code works as intended, 
    it's just used in a wrong way.
    
    This kind of exception will be usually caught and turned into a 4** response code'''
    status = 400

class ProgrammingError(Error):
    '''Exception strongly suggesting a bug.'''
    status = 500

class ServerError(Error):
    '''We don't know what happened, but we're pretty sure this should not be possible.'''
    status = 500
