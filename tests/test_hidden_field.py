'''
Test field with hidden=True.

Hidden field:
    *   is not visible
    *   might not be modified
This leads to a question - what is the difference between hidden field and no field at all?
Answer: 
    *   hidden field could be used by other, non-hidden Calc field.
        Combination "hidden scalar/rel field(s) + calc field(s)" allows as to define any interface,
        possibly without any direct relation to stored value(s). In an extreme case, we could have 
        only Calc non-hidden fields.

    *   for connected Rel fields, relation data is usually stored only on one side, and we might want only the
        non-stored field to be accessible. For example, in PGStorage relation between cookie and jar is stored
        on cookie.jar field. If we want fully-working jar.cookies field, without cookie.jar field, the only 
        way is to hide cookie.jar field

Note: Calc fields can't be hidden.

TEST 1
*   Datamodel: example/cookies
*   Modification: 
    *   field cookie.type becomes hidden
    *   cookie gets a Calc field 'is_shortbread':
        *   getter returns true for type=shortbread, false for others
        *   setter sets either 'shortbread' or 'not_shortbread' to cookie.type

TEST 2
*   Datamodel: example/cookies
*   Modification: 
    *   field cookie.jar becomes hidden
    *   cookie gets read-only boolean field in_jar

TEST 3:
*   Attempt to create hidden Calc field should fail

'''

from blargh.data_model.fields import Calc
from blargh.engine import dm
from example import cookies

import pytest

class TestIsShortbread():
    def test_is_shortbread_1(self, init_world, get_client):
        '''Type is not in visible'''
        client = self._prepare_client(init_world, get_client)
        assert 'type' not in client.get('cookie', 1)[0]
    
    def test_is_shortbread_2(self, init_world, get_client):
        '''Type is not settable in PATCH'''
        client = self._prepare_client(init_world, get_client)
        data, status, headers = client.patch('cookie', 1, {'type': 'biscuit'})
        assert status == 400
        assert data == {'error': {'code': 'FIELD_DOES_NOT_EXISTS',
                                  'details': {'field_name': 'type', 'object_name': 'cookie'}}}
    
    def test_is_shortbread_3(self, init_world, get_client):
        '''Type is not settable in POST'''
        client = self._prepare_client(init_world, get_client)
        data, status, headers = client.post('cookie', {'type': 'biscuit'})
        assert status == 400
        assert data == {'error': {'code': 'FIELD_DOES_NOT_EXISTS',
                                  'details': {'field_name': 'type', 'object_name': 'cookie'}}}
    
    def test_set_is_shortbread(self, init_world, get_client):
        '''Check if is_shortbread works as expected'''
        client = self._prepare_client(init_world, get_client)
        assert client.get('cookie', 1)[0]['is_shortbread'] is False
        assert client.get('cookie', 3)[0]['is_shortbread'] is True

        assert client.patch('cookie', 1, {'is_shortbread': True})[1] == 200
        assert client.patch('cookie', 3, {'is_shortbread': False})[1] == 200
        
        assert client.get('cookie', 1)[0]['is_shortbread'] is True
        assert client.get('cookie', 3)[0]['is_shortbread'] is False


    def _prepare_client(self, init_world, get_client):
        init_world(cookies.dm)
        self._hide_type_add_is_shortbread()
        return get_client()
    
    @staticmethod
    def _hide_type_add_is_shortbread():
        def getter(instance):
            type_field = instance.model.field('type')
            return instance.get_val(type_field).stored() == 'shortbread'

        def setter(instance, is_shortbread):
            new_type = 'shortbread' if is_shortbread else 'not_shortbread'
            return {'type': new_type}

        cookie = dm().object('cookie')
        cookie.field('type').hidden = True
        cookie.add_field(Calc('is_shortbread', getter=getter, setter=setter))

class TestHiddenRel():
    def test_hidden_jar_1(self, init_world, get_client):
        '''Check if cookie.jar is not visible'''
        client = self._prepare_client(init_world, get_client)
        assert 'jar' not in client.get('cookie', 1)[0]
    
    def test_hidden_jar_2(self, init_world, get_client):
        '''Check if jar.cookies still works as expected'''
        client = self._prepare_client(init_world, get_client)
        assert client.patch('jar', 1, {'cookies': [1, 2, 3]})[1] == 200
        assert client.get('jar', 2)[0]['cookies'] == []
    
    def test_hidden_jar_3(self, init_world, get_client):
        '''Check if cookie.in_jar'''
        client = self._prepare_client(init_world, get_client)
        assert client.get('cookie', 1)[0]['in_jar'] is True
        assert client.patch('jar', 1, {'cookies': [2]})[1] == 200
        assert client.get('cookie', 1)[0]['in_jar'] is False
        assert client.patch('jar', 1, {'cookies': [1, 2]})[1] == 200
        assert client.get('cookie', 1)[0]['in_jar'] is True

    def _prepare_client(self, init_world, get_client):
        init_world(cookies.dm)
        self._hide_cookie_jar()
        return get_client()
    
    @staticmethod
    def _hide_cookie_jar():
        def getter(instance):
            jar_field = instance.model.field('jar')
            return bool(instance.get_val(jar_field).stored())

        cookie = dm().object('cookie')
        cookie.field('jar').hidden = True
        cookie.add_field(Calc('in_jar', getter=getter))

def test_create_hidden_calc_field():
    '''Check if attempt to create hidden Calc field fails'''
    Calc('some_field', getter=lambda x: None, hidden=False)
    with pytest.raises(Exception):
        Calc('some_field_2', getter=lambda x: None, hidden=True)
