'''
Test all create_* methods from example directory
'''

import pytest

from blargh.engine import world
from example import family, cookies

from ..helpers.blargh_config import world_data

@pytest.mark.parametrize("create_function", family.create.__all__)
def test_create_family(init_world, create_function):
    init_world(family.dm, create_function)
    assert world_data() == world().data()

@pytest.mark.parametrize("create_function", cookies.create.__all__)
def test_create_cookies(init_world, create_function):
    init_world(cookies.dm, create_function)
    assert world_data() == world().data()
