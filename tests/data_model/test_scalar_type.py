'''
Test type_ of Scalar field
'''

from blargh.data_model.fields import Scalar
from blargh import exceptions
import pytest

params = (
    (None, 1, False),
    (None, '1.1', False),
    (None, 1.1, False),
    (None, '[a, b]', False),
    (str, 1, False),
    (str, '[a, b]', False),
    (int, 1, False),
    (int, '1', False),
    (int, '1.1', True),
    (int, 1.1, True),
    (int, '[a, b]', True),
    (float, 1, False),
    (float, '1', True),  # str(float('1')) is '1.0', so they are not equal
    (float, '1.1', False),
    (float, '[a, b]', True),
)
@pytest.mark.parametrize('type_, value, raises', params)
def test_scalar_type(type_, value, raises):
    field = Scalar('some_field', type_=type_)
    if raises:
        with pytest.raises(exceptions.BadFieldValue):
            field.val(value)
    elif type_:
        assert field.val(value)._val == type_(value)
    else:
        assert field.val(value)._val == value
