Data model
==========

`Example data model in quickstart <quickstart.html#data-model>`__

Overview
--------

Data model definition is a core part of any blargh-based application.
In brief, there are four steps:

.. code-block:: python

    from blargh import data_model

    #   STEP 1 - initialize the data model
    dm = data_model.DataModel('some_name')

    #   STEP 2 - create some objects
    object_1 = dm.create_object('object_1_name')
    object_2 = dm.create_object('object_2_name')
    
    #   STEP 3 - add fields to objects
    object_1.add_field(data_model.fields.SomeField('some_field_name', ...))
    object_2.add_field(data_model.fields.OtherField('other_field_name', ...))

    #   STEP 4 - (optional) connect different objects
    dm.connect(object_1, 'some_field_name', object_2, 'other_field_name')

Steps 1,2 and 4 are simple declarations, all the magic happens in :code:`data_model.fields`.

Fields
------

.. autoclass:: blargh.data_model.fields.Field

.. autoclass:: blargh.data_model.fields.Scalar

.. autoclass:: blargh.data_model.fields.Calc

.. autoclass:: blargh.data_model.fields.Rel


Creating custom fields
----------------------

Connecting Rel fields
---------------------

Let's consider mother-child data model:

.. code-block:: python

    from blargh.data_model import DataModel
    from blargh.data_model.fields import Scalar, Rel

    dm = data_model.DataModel('mother_and_child')

    mother = dm.create_object('mother')
    child = dm.create_object('child')
    
    mother.add_field(Scalar('id', pkey=True, type_=int))
    mother.add_field(Rel('children', stores=child, multi=True))

    child.add_field(Scalar('id', pkey=True, type_=int))
    child.add_field(Rel('mother', stores=mother, multi=False))

In this data model, mother has any number of children, and child could have at most one mother.
What's still missing is the connection between "A is mother of B" and "B is one of A's children". 
In standard mother-has-child-data-model those two statements are interchangeable, which is coded by:

.. code-block:: python

    dm.connect(mother, 'children', child, 'mother')

This way, e.g:

*   if we remove an element from :code:`mother.children`, removed child looses mother
*   if we set :code:`child.mother`, :code:`mother.children` field also get's updated for both
    new mother and (possible) previous mother.

NOTE: This mother-child connection is by no way necesary, e.g. :code:`mother.children` 
could refer to biological children only, and child could have adoptive mother.

Utilities
---------

:code:`dm.as_code()` returns code lines that create identical data model

.. code-block:: python
    
    dm = ... # any data model declaration
    with open('some_file.py', 'w') as f:
        f.write("\n".join(dm.as_code()))

    from some_file import dm as dm_2
    assert dm == dm_2

[TODO - data model from PG database]
