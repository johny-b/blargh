'''
Test Calc field with setter.

We add field 'cookie_cnt' to cookies.jar, working as follows:
    *   using it in GET context returns number of cookies
    *   using it when modyfying jar:
        *   does nothing, when jar has this number of cookies
        *   fills jar with fresh anonymous cookies, if there were to little
        *   removes (last) cookies from jar, if there were too many
'''

from blargh.data_model.fields import Calc
from blargh.engine import dm
from example import cookies

import pytest

def add_cookie_cnt_field():
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

    jar_obj = dm().object('jar')
    jar_obj.add_field(Calc('cookie_cnt', getter=getter, setter=setter))


def test_getter(init_world, get_client):
    '''
    Test if getter alone works as expected
    '''
    init_world(cookies.dm)
    add_cookie_cnt_field()
    client = get_client()
    assert client.get('jar', 1)[0]['cookie_cnt'] == 2
    assert client.get('jar', 2)[0]['cookie_cnt'] == 1
    client.post('jar', {})
    assert client.get('jar', 3)[0]['cookie_cnt'] == 0
    client.post('jar', {'cookies': [{}, {}, {}]})
    assert client.get('jar', 4)[0]['cookie_cnt'] == 3

@pytest.mark.parametrize("cookie_cnt", (0, 1, 2, 3))
def test_setter_post_put(init_world, get_client, cookie_cnt):
    '''
    Create new jar with given number of cookies
    '''
    init_world(cookies.dm)
    add_cookie_cnt_field()
    client = get_client()

    assert client.put('jar', 3, {'cookie_cnt': cookie_cnt})[1] == 201
    assert len(client.get('jar', 3)[0]['cookies']) == cookie_cnt

    assert client.post('jar', {'cookie_cnt': cookie_cnt})[1] == 201
    assert len(client.get('jar', 4)[0]['cookies']) == cookie_cnt

@pytest.mark.parametrize("jar_id", (1, 2))
@pytest.mark.parametrize("cookie_cnt", (0, 1, 2, 3))
def test_setter_patch(init_world, get_client, jar_id, cookie_cnt):
    '''
    Patch existing jar to given number of cookies
    '''
    init_world(cookies.dm)
    add_cookie_cnt_field()
    client = get_client()

    client.patch('jar', jar_id, {'cookie_cnt': cookie_cnt})
    assert len(client.get('jar', jar_id)[0]['cookies']) == cookie_cnt
