'''
Test PGStorage where:
    *   user_id: ... is required to make any call
    *   cookies and jars have "user_id" column, with owner id
    *   any user might create cookie/jar, users are allowed to modify only their
        cookies/jars
'''
from blargh import engine, exceptions
from tests.helpers.blargh_config import init_pg_world
from example import cookies

class UserIdQuery(engine.storage.pg.Query):
    def _user_id(self):
        auth = engine.world().get_auth()
        if not auth or 'user_id' not in auth:
            raise exceptions.e401()
        return auth['user_id']
    
    def select(self, name, data):
        data['user_id'] = self._user_id()
        return super().select(name, data)

    def upsert(self, name, data):
        data['user_id'] = self._user_id()
        return super().upsert(name, data)

def init_cookies_with_user_id():
    '''
    Init cookies world with user_id.
    Cookies 1, 2 and jar 1 are owned by user 1, others - by user 2.
    '''
    def set_query_class(query_cls):
        '''
        Make tester use CLS as query
        '''
        def wrap_storage(f):
            def wrapped_storage(*args, **kwargs):
                old_storage = f(*args, **kwargs)
                new_storage = engine.PGStorage(old_storage._conn, old_storage._schema, query_cls=query_cls)
                return new_storage
            return wrapped_storage
    
        engine.config._config['create_storage'] = wrap_storage(engine.config._config['create_storage'])

    #   1.  Init world
    init_pg_world(cookies.dm)
    
    #   2.  Modify cookie/jar tables 
    conn = engine.world().storage._conn
    conn.cursor().execute('''
        ALTER TABLE jar     ADD COLUMN user_id integer;
        ALTER TABLE cookie  ADD COLUMN user_id integer;
        UPDATE jar      SET user_id = 2 - (id < 2)::integer;
        UPDATE cookie   SET user_id = 2 - (id < 3)::integer;
    ''')
    conn.commit()

    #   3.  Set query class
    set_query_class(UserIdQuery)

