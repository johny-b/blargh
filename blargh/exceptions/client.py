from .base import ClientError

class e400(ClientError):
    status = 400
    code = 'bad_request'

class e401(ClientError):
    status = 401
    code = 'unauthorized'

class e404(ClientError):
    status = 404
    code = 'object_does_not_exist'

class e422(ClientError):
    status = 422
    code = 'unprocessable_entity'

class FieldDoesNotExist(e400):
    code = 'field_does_not_exists'

class FieldIsReadonly(e400):
    code = 'field_is_readonly'

class FieldUpdateForbidden(e400):
    code = 'field_update_forbidden'

class SearchForbidden(e400):
    code = 'search_forbidden'

class BadParamValue(e400):
    code = 'bad_param_value'

class BadFieldValue(e400):
    code = 'bad_field_value'
