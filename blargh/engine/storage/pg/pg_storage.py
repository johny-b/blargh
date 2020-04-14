'''
CURRENT ASSUMPTIONS:
    *   all tables are in a single schema
    *   tables have the same names as resources
'''

from ..base_storage import BaseStorage
from blargh.engine import dm
from .query import Query

from .... import exceptions
import psycopg2

def capture_psycopg_error(f):
    def wrapped(self, *args, **kwargs):
        def diag_2_msg(diag):
            # print(diag.message_primary)
            return diag.message_primary
            # return "{}\n{}".format(diag.message_primary, diag.message_detail)
        try:
            return f(self, *args, **kwargs)
        except psycopg2.extensions.TransactionRollbackError as e:
            #   Either transaction was not serializable, or some deadlock was detected.
            #   Whatever happened, it makes sense to run this operation again.
            raise exceptions.TransactionConflictRetriable()
        except psycopg2.InterfaceError as e:
            raise exceptions.e500(diag_2_msg(e.diag))
        except psycopg2.Error as e:
            raise exceptions.e400(diag_2_msg(e.diag))
            
    return wrapped


class PGStorage(BaseStorage):
    def __init__(self, conn, schema, query_cls=Query):
        #   This construction is purely to avoid wrapping __init__
        self._true_init(conn, schema, query_cls)

    @capture_psycopg_error
    def _true_init(self, conn, schema, query_cls):
        #   Modify connection
        if conn.status is not psycopg2.extensions.STATUS_READY:
            conn.commit()
        conn.set_session(isolation_level='SERIALIZABLE', autocommit=False)
        conn.cursor().execute('''SET CONSTRAINTS ALL DEFERRED''')
        
        self._conn = conn

        self._schema = schema

        #   To initialize query instance we need list of all primary keys. Those are available
        #   in the data model, but it seems a good idea to avoid passing data model directly to storage.
        #   Instead, self._query is built in lazy way, when needed - and that should be after engine
        #   was set up, so the data model is available in dm() function.
        self._query_cls = query_cls
        self._query = None

    def _q(self):
        if self._query is None:
            self._query = self._query_cls(self._conn, self._schema, 
                                          {o.name: o.pkey_field().name for o in dm().objects().values()})
        return self._query
    
    #   PUBLIC INTERFACE
    @capture_psycopg_error
    def save(self, instance):
        #   If we got here, instance.changed() is True, but all changes could be made
        #   on "virtual" columns (rel fields stored on the other side). In such case,
        #   nothing is saved, because no database columns changed.
        table_columns = self._q().table_columns(instance.model.name)
        changed_columns = [f.name for f in instance.changed_fields if f.name in table_columns]
        if not changed_columns:
            return

        #   Create representation
        data = self._write_repr(instance)

        #   Save new value
        name = instance.model.name
        self._q().upsert(name, data)

    def _write_repr(self, instance):
        '''
        Returns INSTANCE representation including all columns that will be written to the database.
        This means 
            *   all values other than None
            *   None values, if they were explicitly set (by INSTANCE.update() -> they are in INSTANCE.changed_fields
        '''
        #   1.  Create dictionary with all columns that should be written to the database
        data = {}

        for field, val in instance.field_values():
            if not field.stored():
                continue
            
            #   If val.stored() is None it should be written only if field changed.
            #   This way we distinguish None fields that were never set before (and might be set to
            #   a different value by database default) from updated fields set to None.
            if val.stored() is None and field not in instance.changed_fields:
                continue

            data[field.name] = val.stored()

        #   2.  Add primary key value (if this is a fresh instance, it is already in data)
        pkey_name = instance.model.pkey_field().name
        data[pkey_name] = instance.id()

        #   3.  Remove keys not matching database columns
        clean_data = self._remove_virtual_columns(instance.model.name, data)

        return clean_data

    @capture_psycopg_error
    def load(self, name, id_):
        return self.load_many(name, [id_])[0]

    @capture_psycopg_error
    def load_many(self, name, ids):
        if not ids:
            return []

        #   Determine column name
        pkey_name = dm().object(name).pkey_field().name
        
        stored_data = self._select_objects(name, {pkey_name: ids})
        if len(stored_data) != len(ids):
            got_ids = [d[pkey_name] for d in stored_data]
            missing_ids = [id_ for id_ in ids if id_ not in got_ids]
            raise exceptions.e404(object_name=name, object_id=missing_ids[0])
        
        full_data = self._add_virtual_columns(name, stored_data)
        return full_data

    @capture_psycopg_error
    def begin(self):
        #   All necesary things were set in __init__(autocommit, deferrable constraints),
        #   so begin does nothing
        pass

    @capture_psycopg_error
    def commit(self):
        self._conn.commit()

    @capture_psycopg_error
    def rollback(self):
        self._conn.rollback()

    @capture_psycopg_error
    def delete(self, name, id_):
        self._q().delete(name, id_)

    @capture_psycopg_error
    def selected_ids(self, this_name, wr, sort, limit):
        '''
        Return IDs from table NAME matching WR. 
        SORT and LIMIT are ignored (storages are allwed to ignore those parameters, they are applied
        later in Enigne.get).

        HOW IT SHOULD BE DONE

        1. WR is interpreted as WHERE
        2. SORT becomes ORDER BY
        3. LIMIT becomes LIMIT
        and everything is processed in a single query.

        That would be easy if we assumed that all REL fields have information stored in THIS_NAME table
        but unfortunately REL field could be stored on any table, so instead
        of WHEREs we might get some JOINS and this becomes more complicated.

        HOW IT IS CURRENLY DONE

        1.  WR is split into two parts:
            *   one select for THIS_NAME table with all possible WHEREs
            *   one select for each joined table with REL field stored on the other side
        2.  Intersection of IDs from all selects is returned
        3.  SORT and LIMIT are ignored. SORT is ignored because there is no way of implementing it
            different from both:
                *   HOW IT SHOULD BE DONE above
                *   sorting in Engine.get
            and LIMIT is ignored because SORTing first is necesary.
        '''
        model = dm().object(this_name)
        
        #   First, split to parts
        this_table_wr = {}
        other_selects = []
        for key, val in wr.items():
            if key in self._q().table_columns(this_name):
                this_table_wr[key] = val
            else:
                field = model.field(key)
                other_name = field.stores.name
                other_field_name = field.other.name
                other_pkey_name = dm().object(other_name).pkey_field().name
                other_selects.append((other_name, other_field_name, {other_pkey_name: val}))

        #   List of sets of ids, to be intersected later
        sets_of_ids = []

        #   This table ids
        this_table_objects = self._select_objects(this_name, this_table_wr)
        this_pkey_name = model.pkey_field().name
        sets_of_ids.append(set([x[this_pkey_name] for x in this_table_objects]))

        #   Other tables ids
        for other_name, other_fk_name, other_table_wr in other_selects:
            other_table_objects = self._select_objects(other_name, other_table_wr)
            sets_of_ids.append(set([x[other_fk_name] for x in other_table_objects]))

        #   Final ids
        return sorted(set.intersection(*sets_of_ids))

    @capture_psycopg_error
    def _select_objects(self, name, wr):
        '''
        WR containst key-val pairs matching columns in table NAME.
        List of dictionaries from table NAME is returned.
        '''
        return self._q().select(name, wr)

    @capture_psycopg_error
    def next_id(self, name):
        '''
        If NAME primary key column has default value, it is returned.
        This works well with
            *   nextval(sequence)
            *   any simmilar user-defined function
        
        If there is no default, an exception is raised. This might change and one
        day we'll look for the biggest current ID and add 1.

        NOTE: Any value returned by any generator might be already taken, if client set it 
        in an explicit way (probably via PUT). Generator is called repeatedly, until we
        find a non-duplicated value. This might take long, if there were many PUT's, 
        but next time, it will probably be fast (if nextval(sequence) is used).
        Also:
            *   if generator returns twice the same value, exception is raised
            *   maybe this could be done better? Note - we want to handle also other than nextval() defaults,
                i.e. dependant on now().

        '''
        pkey_name = dm().object(name).pkey_field().name
        default_expr = self._q().default_pkey_expr(name, pkey_name)

        if default_expr is None:
            raise exceptions.ProgrammingError("Unknown default pkey value for {}".format(name)) 
        
        old_val = None
        while True:
            cursor = self._conn.cursor()
            cursor.execute("SELECT {}".format(default_expr))
            val = cursor.fetchone()[0]
            if self._select_objects(name, {pkey_name: val}):
                if old_val == val:
                    raise exceptions.ProgrammingError('Pkey value generator returned twice the same value. \
                                                      Table: {}, val: {}'.format(name, val))
                else:
                    old_val = val
            else:
                return val

    @capture_psycopg_error
    def data(self):
        d = {}
        for name, obj in dm().objects().items():
            d[name] = self._q().dump_table(name, obj.pkey_field().name)
        return d


    #   PRIVATE METHODS

    def _remove_virtual_columns(self, name, data):
        '''
        DATA contains all "possible" column values.

        Some of those need to be written to the database, but other are
        redundat (i.e. if we have relation parent-child, probably child table has
        something like 'parent_id', but parent table has no 'children' column, so
        it might not be written) and they need to be removed now.

        This operation should reverse _add_virtual_columns.
        '''
        clean_data = {}
        for key, val in data.items():
            if key in self._q().table_columns(name):
                clean_data[key] = val
        return clean_data

    def _add_virtual_columns(self, this_name, data):
        '''
        DATA contains only values stored in table NAME.
        We need to fill relationship fields based on other tables.

        I.e. if we have parent-child relationship probably child table has
        'parent_id', and parent has no 'children' column, 
        so if NAME == 'parent' we need to add 'children' key in data, 
        based on relationship fields.

        This operation should reverse _remove_virtual_columns.
        '''
        #   Determine IDs
        pkey_name = dm().object(this_name).pkey_field().name
        ids = [d[pkey_name] for d in data]

        for field in dm().object(this_name).fields():
            name = field.name
            if field.rel and name not in data[0]:
                other_name = field.stores.name
                other_field_name = field.other.name
                all_related = self._select_objects(other_name, {other_field_name: ids})

                related_pkey_name = dm().object(other_name).pkey_field().name
                for el in data:
                    this_related = [x for x in all_related if x[other_field_name] == el[pkey_name]]
                    related_ids = [x[related_pkey_name] for x in this_related]
                    if field.multi:
                        el[name] = related_ids
                    else:
                        el[name] = related_ids[0] if related_ids else None
        return data
