from abc import ABC, abstractmethod

class BaseStorage(ABC):
    '''
    Abstract base class for all Storage classes.

    While designing class, especially __init__, it's good to remember that
    engine.setup() accepts either an initialized Storage, or function returning new
    Storage, and if function is provided, new Storage instance will be created
    **for every request**, so it's recomented to either:
      * provide object, not function, if possible,
      * or make Storage initialization as simple as possible (e.g. avoid reading large files)
    '''
    
    @abstractmethod
    def __init__(self):
        '''
        Initialize storage object.
         '''

    @abstractmethod
    def save(self, instance):
        '''
        :param instance: :code:`blargh.engine.Instance` with already set :code:`.id()`.
        :returns: None

        Save single object to the database. If such object already exists, it should be replaced.
        This method is an inverse of .load().
        '''

    @abstractmethod
    def load(self, name, id_):
        '''
        :param name: resource name
        :param id_: resource id
        :returns: dict

        Return dictionary with all saved data for object identified by (name, id_).
        This method is an inverse of .save().
        '''

    @abstractmethod
    def delete(self, name, id_):
        '''
        :param name: resource name
        :param id_: resource id
        :returns: None
        
        Remove from storage object identified by (name, id_).
        Should raise exceptions.e404 if object does not exists.
        '''

    @abstractmethod
    def selected_ids(self, name, data, sort, limit):
        '''
        :param name: resource name
        :param data: dict, with resource field names as keys
        :param sort: list of field names instances should be sorted with, with possible '-' prefixes 
                     indicating descending order, storage does not have to implement this
        :param limit: non-negative integer indicating max number of instances that should returned,
                      storage does not have to implement this (and should not if it does not implement sort)
        :returns: sorted list of ids

        Return list of ids of all objects for which data is a subset of value returned by .load().

        In other words:

        .. code-block:: python

            for id_ in Storage.selected_ids('foo', {'bar': 'baz'}):
                assert Storage.load('foo', id_)['bar'] == 'baz'
        '''

    @abstractmethod
    def next_id(self, name):
        '''
        :param name: resource name
        :returns: next free id

        There is no guarantee this id will be used, but no value
        should ever be returned more than once.

        This method is required only for creation of POSTed resources
        (or created in any other way without supplying id), so Storage might
        just raise some exception if all resources should be created via PUT.
        '''

    @abstractmethod
    def begin(self):
        '''
        Start a transaction, that will be later .commit()ed or .rollback()ed.

        Togehter with .commit() and .rollback() provides transctional interface.
        Might be left empty if this Storage does not support transactions.
        '''

    @abstractmethod
    def commit(self):
        '''
        Save all changes since last .begin().

        Togehter with .begin() and .rollback() provides transctional interface.
        Might be left empty if this Storage does not support transactions.
        '''

    @abstractmethod
    def rollback(self):
        '''
        Discard all changes since last .begin().

        Togehter with .begin() and .commit() provides transctional interface.
        Might be left empty if this Storage does not support transactions.
        '''
    
    @abstractmethod
    def data(self):
        '''
        :returns: all storage data in any convinient format.

        Used **only** for debugging & testing.
        '''
