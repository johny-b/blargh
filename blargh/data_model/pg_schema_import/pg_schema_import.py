'''Create DataModel object matching all tables in given Postgresql schema

Note: created DataModel
    *   will work well in with blargh.storage.PG
    *   in no way is a complete imitation of PostgreSQL data_model.
        For example, defaults are ignored - they will be applied on
        the database side.
'''

from .. import DataModel
from .query import Query
from collections import defaultdict
from blargh.data_model.fields import Scalar, Rel

class PGSchemaImport():
    def __init__(self, conn, name, data_model_cls=DataModel):
        self._name = name
        self._q = Query(conn)
        
        self._dm = data_model_cls(self._name)

        #   Each foreign key field determines one relationship.
        #   Foreign key fields are gathered in _create_objects()
        #   and later used in _create_relationships().
        self._fk_columns = defaultdict(set)
        
        self._create_objects()
        self._create_relationships()

    def data_model(self):
        '''Return data_model, created during initialisation'''
        return self._dm

    def _create_objects(self):
        '''Create all objects

        Each object has scalar fields corresponding to all columns in the database,
        except FOREIGN KEY columns, which are used to create relationships further.

        PRIMARY KEY is also set.
        '''
        #   All table names, without schema
        table_names = self._q.get_table_names_in_schema(self._name)
        for table_name in sorted(table_names):

            #   Create object
            obj = self._dm.create_object(table_name)

            #   Create all scalar fields
            columns = self._q.get_columns_data(self._name, table_name)
            
            for column in columns:
                if column['fkey']:
                    #   This will be used further, in _create_relationship
                    self._fk_columns[table_name].add(column['name'])
                else:
                    #   Note: default is always 'None', because we don't want to
                    #   duplicate internal PostgreSQL defaults
                    obj.add_field(Scalar(column['name'], pkey=column['pkey'], default=None, type_=column['type']))

    def _create_relationships(self):
        '''Create all relationships

        Note: Columns that are simultaneously PRIMARY KEY and FOREIGN KEY are forbidden.
              This simplification is requred by current DataModel, where relationship fields
              are not allowed to be primary keys. This might change in the future.
        Note 2: Each relationship is between "two tables", but table might reference itself,
                so this are not necesary two different tables.

        Possible relationships could be divided into two groups:

        A) Without 'join' table

        Relationships without additional 'join table' are defined by single
        FOREIGN KEY column. Owner of this column will be called 'child', table
        pointed by FK constraint - 'parent'. Possible relationships:
            CHILD       PARENT      CONSTRAINT
            0 .. n      0 .. 1      FOREIGN KEY
            0 .. n      1 .. 1      FOREIGN KEY NOT NULL
            0 .. 1      0 .. 1      FOREIGN KEY UNIQUE
            0 .. 1      1 .. 1      FOREIGN KEY NOT NULL UNIQUE
        
        B) With 'join' table
        
        All other relationships that could be clearly defined by database structure require
        additional join table (reminder: PRIMARY KEY FOREIGN KEY columns are forbidden).

        Such relationships are not handled it any clever way. Join table representes additional object,
        referenced in a "simple" way (described in A) by both other tables.
        '''

        #   For each foreign key field we create two Rel fields and connect them.
        #   "Child" is - as above - object with FK field.
        for child_name, column_names in self._fk_columns.items():
            for child_column_name in column_names:
                #   relationship data, check Query.get_rel_data for description
                parent_name, child_card, parent_card, child_cascade = \
                        self._q.get_rel_data(self._name, child_name, child_column_name)
                
                #   objects
                child = self._dm.object(child_name)
                parent = self._dm.object(parent_name)
                
                #   "multi" fields are '*'/'+', single are '?' and '1'
                child_multi = child_card in ('*', '+')
                parent_multi = parent_card in ('*', '+')

                #   name of the other side virtual (-> not a column) field
                parent_column_name = self._default_parent_field_name(child, parent, child_card, child_column_name)

                #   create fields
                child.add_field(Rel(child_column_name, stores=parent, multi=parent_multi, cascade=child_cascade))
                parent.add_field(Rel(parent_column_name, stores=child, multi=child_multi, cascade=False))
                
                #   and connect them
                self._dm.connect(child, child_column_name, parent, parent_column_name)
    
    def _default_parent_field_name(self, child, parent, card, child_field_name):
        '''
        Default name of PARENT field storing CARD number of CHILD. Field is connected 
        to CHILD_FIELD_NAME.

        If CHILD_FIELD_NAME does not start with PARENT.name, (i.e. '{}_id'.format(PARENT.name)),
        we assume it has a certain meaning, and return {}_of.(format(CHILD_FIELD_NAME).
        E.g., when PARENT.name == 'female' and CHILD_FIELD_NAME == 'mother' we get 'mother_of'.

        Otherwise
            * for single   CARD we return OTHER.name
            * for multiple CARD we return OTHER.name + 's'
        e.g., when OTHER.name is 'child' we get either 'child' or 'childs'.
        
        Note: this names are not final - in case of duplicates, integer suffixes are added, 
              so finnaly we might end up with fields (mother_of, mother_of1, mother_of2, ... ).

        '''
        if child_field_name.startswith(parent.name):
            name = child.name
            if card in ('*', '+'):
                name += 's'
        else:
            name = '{}_of'.format(child_field_name)

        #   Update in case of duplicates
        i = 1
        while True:
            if parent.field(name) is None:
                return name
                
            name += str(i)
            i += 1
