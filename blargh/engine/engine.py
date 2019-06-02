from . import init_world
from .. import exceptions
from . import conf

def world_transaction(f):
    def wrapped(*args, **kwargs):
        def run_with_retry(retry_cnt):
            '''
            Return result of F(world, *ARGS, **KWARGS).
            If exceptions.TransactionConflictRetriable is raised, and RETRY_CNT > 0,
            try again with RETRY_CNT - 1.
            '''
            try:
                world.begin()
                result = f(world, *args, **kwargs)
                world.write()
                world.commit()
            except exceptions.TransactionConflictRetriable as e:
                world.rollback()
                if retry_cnt > 0:
                    result = run_with_retry(retry_cnt - 1)
                else:
                    raise exceptions.e500
            return result

        #   Initialize world
        world = init_world()

        #   world has already set auth -> this is something strange
        if world.get_auth():
            raise exceptions.ProgrammingError("world with auth already set should be impossible here")

        #   'auth' in kwargs -> remove it and send to world
        if 'auth' in kwargs:
            auth = kwargs.pop('auth')

            #   auth = None is the same as empty dict
            if auth is None:
                auth = {}
            
            #   auth should be a dict
            if type(auth) is not dict:
                raise exceptions.e500("auth should be a dict")
            world.set_auth(auth)
        
        #   Start work
        try:
            result = run_with_retry(conf['max_retry_cnt'])
        except Exception as e:
            world.rollback()
            raise e
        finally:
            #   Whatever happened, auth data should be removed
            world.remove_auth()
        return result
    return wrapped

class Engine():
    @world_transaction
    def get(world, name, id_=None, filter_={}, depth=1):
        if id_ is not None:
            instance = world.get_instance(name, id_)
            return instance.repr(depth), 200
        else:
            instances = world.get_instances(name, filter_)
            return [instance.repr(depth) for instance in instances], 200
    
    @world_transaction
    def post(world, name, val):
        '''
        VAL is either a dictionary, or a collection of dictionaries
        '''
        def single_post(d):
            i = world.new_instance(name)
            i.update(d)
            world.write()
                
            #   Some field might be modified at write() (i.e. by database defaults),
            #   we want to include them in final data
            i = world.get_instance(name, i.id())
            return i.repr(1)

        if type(val) is list:
            data = [single_post(x) for x in val]
        elif type(val) is dict:
            data = single_post(val)
        else:
            raise exceptions.ProgrammingError('post accepts list or dict, nothing else')
            
        return data, 201
    
    @world_transaction
    def patch(world, name, id_, val):
        i = world.get_instance(name, id_)
        i.update(val)
        world.write()
                
        #   Some field might be modified at write() (i.e. by database triggers),
        #   we want to include them in final data
        i = world.get_instance(name, i.id())
        
        #   We return repr(1) + updated fields from repr(1)
        data = i.repr(1)
        return data, 200
    
    @world_transaction
    def put(world, name, id_, val):
        #   Delete, ignoring 404
        try:
            i = world.get_instance(name, id_)
            i.delete()
        except exceptions.e404:
            pass
        
        #   Create new instance
        i = world.new_instance(name, id_)
        i.update(val)
        world.write()
                
        #   Some field might be modified at write() (i.e. by database defaults),
        #   we want to include them in final data
        i = world.get_instance(name, i.id())
    
        data = i.repr(1)
        return data, 201
    
    @world_transaction
    def delete(world, name, id_):
        i = world.get_instance(name, id_)
        i.delete()
        
        return None, 200
    
