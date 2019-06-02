from .base import ServerError

class e500(ServerError):
    code = 'server_error'
    status = 500

class TransactionConflictRetriable(e500):
    pass
