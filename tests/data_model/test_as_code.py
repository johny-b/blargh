'''
DataModel.as_code() should return the same DataModel.

This is a little redudnat, since equality is testes with .as_code() : )
but equality might be one day tested better.
'''

from example.cookies import dm as cookies_dm
from example.family import dm as family_dm

import pytest
import importlib

@pytest.mark.parametrize("tested_dm", [cookies_dm, family_dm])
def test_examples_as_code(tested_dm):
    #   data model code
    dm_code_lines = tested_dm.as_code()
    
    #   create file, to make "real" import
    fname = 'tests/_dm.py'
    with open(fname, 'w') as f:
        f.write("\n".join(dm_code_lines))

    #   import created file 
    #   (reloading is be necesary - there is more than one datamodel tested)
    from tests import _dm
    importlib.reload(_dm)

    #   test (example datamodels export 'dm' variable)
    assert tested_dm == _dm.dm


dm_1 = '''\
from blargh.data_model.data_model import DataModel
from blargh.data_model.fields import Scalar, Rel, Calc

dm = DataModel('test_as_code')
o = dm.create_object('o')
o.add_field(Scalar('f1', ext_name='f1', writable=True, readonly=True, hidden=False, default=None, pkey=True, type_=int))
'''
dm_2 = '''\
from blargh.data_model.data_model import DataModel
from blargh.data_model.fields import Scalar, Rel, Calc
dm = DataModel('test_as_code')
o = dm.create_object('o')
def getter(instance):
    return 'some things never change'

def setter(instance, val):
    return {'f2': 'aaa'}

o.add_field(Calc('c1', ext_name='c1', writable=True, readonly=False, hidden=False, default=None, getter=getter, setter=setter))
o.add_field(Scalar('f1', ext_name='f1', writable=True, readonly=True, hidden=False, default=None, pkey=True, type_=int))
o.add_field(Scalar('f2', ext_name='f2', writable=True, readonly=True, hidden=False, default=None, pkey=False, type_=None))
o.add_field(Scalar('f3', ext_name='f3', writable=False, readonly=False, hidden=False, default=None, pkey=False, type_=None))
def writable(instance):
    return instance.get_val('f1').repr() == 7

o.add_field(Scalar('f4', ext_name='f4', writable=writable, readonly=False, hidden=False, default=None, pkey=False, type_=None))
'''

dm_3 = '''\
from blargh.data_model.data_model import DataModel
from blargh.data_model.fields import Scalar, Rel, Calc
dm = DataModel('test_as_code')
o1 = dm.create_object('o1')
o1.add_field(Scalar('id', ext_name='id', writable=True, readonly=True, hidden=False, default=None, pkey=True, type_=int))
o2 = dm.create_object('o2')
o2.add_field(Scalar('id', ext_name='id', writable=True, readonly=True, hidden=False, default=None, pkey=True, type_=str))

def writable(instance):
    return False

o1.add_field(Rel('o2s', ext_name='o2s', writable=writable, readonly=False, hidden=False, default=None, stores=o2, multi=False, cascade=True))
o2.add_field(Rel('o1_id', ext_name='o1_id', writable=True, readonly=False, hidden=False, default=[], stores=o1, multi=True, cascade=False))

dm.connect(o2, 'o1_id', o1, 'o2s')'''

@pytest.mark.parametrize("dm_text", (dm_1, dm_2, dm_3))
def test_as_code(dm_text):
    #   1.  Create first data model file
    fname = 'tests/_dm.py'
    with open(fname, 'w') as w:
        w.write(dm_text)
    
    #   2.  Import tested data model
    from tests import _dm
    importlib.reload(_dm)

    #   3.  Create second file, based on imported datamodel
    fname_2 = 'tests/_dm_2.py'
    with open(fname_2, 'w') as f:
        f.write("\n".join(_dm.dm.as_code()))

    #   4.  Find all non-empty, not-comment, not-import lines in both files.. 
    with open(fname, 'r') as f:
        lines_1 = f.readlines()
    with open(fname_2, 'r') as f:
        lines_2 = f.readlines()
    
    def data_model_line(line):
        return not (line.startswith('#') or
                    'import' in line or
                    line.isspace()
                    )
    lines_1 = [l for l in lines_1 if data_model_line(l)]
    lines_2 = [l for l in lines_2 if data_model_line(l)]
     
    #   5.  Compare
    assert lines_1 == lines_2
