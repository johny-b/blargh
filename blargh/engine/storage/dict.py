from .base_storage import BaseStorage

from ... import exceptions
from .. import dm

from copy import deepcopy

class DictStorage(BaseStorage):
    '''Simplest possible Storage, indended for development and ad-hoc applications.
        
        :param data_dict: dict object where all data will be stored
    '''
    def __init__(self, data_dict):
        self._commited = data_dict
        
        #   This is initialized on first "real" usage
        #   (Depends on the data model, and data model might not be defined yet)
        self._max_used_id = None

        #   This is not None between begin and commit/rolback
        self._uncommited = None

    def _data(self):
        if not self._commited:
            empty = self._empty_data()
            self._commited.update(empty)

        if self._uncommited:
            return self._uncommited
        return self._commited

    def _empty_data(self):
        d = {name: {} for name in dm().objects()}
        return d

    def _init_max_used_id(self):
        #   currently used id's - they might not be in self._data yet, but
        #   are reserved and might not be reused
        self._max_used_id = {name: 0 for name in dm().objects()}
    
    #   PUBLIC INTERFACE
    def save(self, instance):
        #   Determine name and id
        name = instance.model.name
        id_ = instance.id()

        #   Remove current object, if exists
        if id_ in self._data()[name]:
            self.delete(name, id_)
        
        #   Create representation
        data = self._write_repr(instance)

        #   Write new object
        self._data()[name][id_] = data

    def _write_repr(self, instance):
        '''
        Returns INSTANCE data structure prepared for storage.
        DictStorage stores only not-null values.
        '''
        d = {}
        for field, val in instance.field_values():
            stored_val = val.stored()
            if stored_val is not None:
                d[field.name] = stored_val
        return d

    def load(self, name, id_):
        return self.load_many(name, [id_])[0]

    def load_many(self, name, ids):
        data = []
        for id_ in ids:
            if id_ not in self._data()[name]:
                raise exceptions.e404(object_name=name, object_id=id_)
        
            instance_data = self._data()[name][id_].copy()

            #   Note: DictStorage stores only not-null values, here we add those Nones
            #   to avoid messing with possible field default values later
            for field in dm().object(name).fields():
                if field.name not in instance_data and field.stored():
                    instance_data[field.name] = None

            data.append(instance_data)
        return data

    def delete(self, name, id_):
        del self._data()[name][id_]

    def selected_ids(self, name, data, **kwargs):
        #   TODO: this is ugly
        items_set = set({k: v for k, v in data.items() if type(v) is not list}.items())
        ids = []
        for id_, stored in self._data()[name].items():
            if items_set.issubset(set({k: v for k, v in stored.items() if type(v) is not list}.items())):
                ids.append(id_)
        return sorted(ids)

    def next_id(self, name):
        '''
        Return next free id for NAME.

        Note: DictStorage assumes all primary keys are numbers (more specific: 
              they have comparison operators and adding one yields bigger one) 
        '''
        #   biggest id in self._data
        max_saved_id = 0 if not self._data()[name] else max(list(self._data()[name]))

        #   biggest of any created instance
        if self._max_used_id is None:
            self._init_max_used_id()
        max_current_id = self._max_used_id[name]

        #   new id
        id_ = max(max_saved_id, max_current_id) + 1
        self._max_used_id[name] = id_
        return id_

    def data(self):
        return self._data()

    def begin(self):
        '''
        More than one begin() changes nothing
        '''
        if self._uncommited is None:
            self._uncommited = deepcopy(self._data())

    def commit(self):
        if self._uncommited is None:
            raise exceptions.ProgrammingError("commit when not in transaction")
        
        for name in self._commited:
            self._commited[name] = self._uncommited[name]

        self._uncommited = None

    def rollback(self):
        if self._uncommited is None:
            raise exceptions.ProgrammingError("rollback when not in transaction")
        self._uncommited = None
