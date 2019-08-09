'''
SORT and LIMIT should work in PGStorage.

To simplyfy tests, we:
    *   disable sorting and limiting in Engine
    *   re-run the same tests as in tests.test_sort_and_limit, using only PGStorage
'''

from tests.test_sort_and_limit import params, prepare
from tests.helpers.blargh_config import init_pg_world
from blargh.engine import Engine

import pytest
import mock

@pytest.mark.parametrize('ids, kwargs', params)
def test_sort_and_limit(get_client, ids, kwargs):
    client = prepare(init_pg_world, get_client)

    with mock.patch.object(Engine, '_apply_sort'):
        with mock.patch.object(Engine, '_apply_limit'):
            data, status_code, _ = client.get('child', depth=0, **kwargs)

            assert status_code == 200
            assert data == ids
