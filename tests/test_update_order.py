'''
TEST 1
When many fields are updated - either via PATCH or when POSTing/PUTing new object - 
they should be processed in order matching data model's fields order.

This makes difference:
    *   for Calc fields with setters somehow dependant on other fields
        (NOTE: it is forbidded to modify the same field twice in one call)
    *   for fields whose writability depends on other fields
(maybe somewhere else too?)

In this tests, we use standard example.cookies and modify it in a following way:
    *   add boolean field 'open' to jar
    *   set cookies' field writable attribute - cookies field might be changed
        only for open jars
    *   add field 'cookie_cnt' to jar - calc field with
        *   getter returning number of cookies
        *   setter removing additional cookies/adding fresh cookies

Two field orders in jar are tested:
    (id, cookies, cookie_cnt, closed)
    (id, closed, cookie_cnt, cookies)

We send PATCHes with more than one field. Patch data + column order determines status.
For example, let's assume we post a new jar:
    {cookie_cnt: 2, closed: True} gives us:
        *   closed jar with two fresh cookies if cookie_cnt is before closed
        *   400, if closed is before cookie_cnt

TEST 2
We add the same 'cookie_cnt' field, either before or after field 'cookies'.
We send both fields and expect different results for different orders.
NOTE: not long ago, this was forbidden, but now is allowed.
'''

import pytest
from example import cookies
from copy import deepcopy
from blargh import engine
from blargh.data_model.fields import Calc, Scalar

def new_cookies_dm(order_id):
    def add_field_closed(dm):
        jar = dm.object('jar')
        jar.add_field(Scalar('closed', default=False))

        #   Add database column if PGStorage
        if issubclass(type(engine.world().storage), engine.PGStorage):
            engine.world().storage._q._conn.cursor().execute('''
                ALTER TABLE jar ADD COLUMN closed boolean;
            ''')
    
    def add_field_cookie_cnt(dm):
        def getter(instance):
            field = instance.model.field('cookies')
            return len(instance.get_val(field).repr(0))
        
        def setter(instance, new_cookie_cnt):
            #   1.  Current state
            cookies_field = instance.model.field('cookies')
            current_cookies = instance.get_val(cookies_field).repr(0)
            current_cookie_cnt = len(current_cookies)
            
            if new_cookie_cnt == current_cookie_cnt:
                #   2A  -   no changes
                new_cookies = current_cookies
            if new_cookie_cnt < current_cookie_cnt:
                #   2B  -   less cookies
                new_cookies = current_cookies[:new_cookie_cnt]
            else:
                #   2C  -   more cookies
                fresh_cookies = [{} for i in range(current_cookie_cnt, new_cookie_cnt)]
                new_cookies = current_cookies + fresh_cookies 

            #   3.  Return value
            return {'cookies': new_cookies}


        jar = dm.object('jar')
        jar.add_field(Calc('cookie_cnt', getter=getter, setter=setter))

    def set_cookies_writable(dm):
        def open_jar(instance):
            return not instance.get_val(instance.model.field('closed')).repr()
        
        jar = dm.object('jar')
        jar.field('cookies')._writable = open_jar


    def set_fields_order(dm, field_names):
        jar = dm.object('jar')
        jar._fields = [jar.field(x) for x in field_names]

    dm = engine.dm()
    add_field_closed(dm)
    add_field_cookie_cnt(dm)
    set_cookies_writable(dm)
    
    orders = {
        1: ('id', 'cookies', 'cookie_cnt', 'closed'),
        2: ('id', 'closed', 'cookie_cnt', 'cookies'),
    }
    set_fields_order(dm, orders[order_id])


data_1 = {'closed': True, 'cookie_cnt': 2} 

params = (
    (data_1, 1, 200, 2, 3),
    (data_1, 2, 400, None, None)
)


@pytest.mark.parametrize("patch_data, order, expected_status, jar_cookies_cnt, all_cookies_cnt", params)
def test_update_order_1(init_world, get_client, patch_data, order, expected_status, jar_cookies_cnt, all_cookies_cnt):
    init_world(deepcopy(cookies.dm))
    new_cookies_dm(order)
    client = get_client()
    data, status, headers = client.patch('jar', 1, patch_data)
    assert status == expected_status
    
    if expected_status < 400:
        assert len(data['cookies']) == jar_cookies_cnt
        data, status, headers = client.get('cookie')
        assert status == 200
        assert len(data) == all_cookies_cnt

params = (
    (1, 'post', ('jar', {'cookies': [], 'cookie_cnt': 1}), 1),
    (2, 'post', ('jar', {'cookies': [], 'cookie_cnt': 1}), 0),
    (1, 'put', ('jar', 1, {'cookies': [1, 2, 3], 'cookie_cnt': 2}), 2),
    (2, 'put', ('jar', 1, {'cookies': [1, 2, 3], 'cookie_cnt': 2}), 3),
    (1, 'put', ('jar', 1, {'cookies': [{}, {}], 'cookie_cnt': 1}), 1),
    (2, 'put', ('jar', 1, {'cookies': [{}, {}], 'cookie_cnt': 1}), 2),
    (1, 'patch', ('jar', 1, {'cookies': [2], 'cookie_cnt': 7}), 7),
    (2, 'patch', ('jar', 1, {'cookies': [2], 'cookie_cnt': 7}), 1),
)

@pytest.mark.parametrize("order_id, method, args, cookie_cnt", params)
def test_update_order_2(init_world, get_client, order_id, method, args, cookie_cnt):
    '''
    It is forbidden to modify the same field in more than one way
    '''
    init_world(deepcopy(cookies.dm))
    new_cookies_dm(order_id)
    client = get_client()

    data, status, headers = getattr(client, method)(*args)
    assert str(status).startswith('2')
    assert len(data['cookies']) == cookie_cnt
    assert data['cookie_cnt'] == cookie_cnt
