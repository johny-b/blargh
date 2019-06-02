from .dict import DictStorage

import pickle

class PickledDictStorage(DictStorage):
    '''
    :param file_name: Name of a file where pickled data will is stored.
                      Empty/missing file is the same as file with empty dictionary.
    '''
    def __init__(self, file_name):
        self._fname = file_name
        d = self._read_file()
        super().__init__(d)

    def commit(self):
        '''
        Commit and write self._commited to file
        '''
        super().commit()
        with open(self._fname, 'wb') as f:
            pickle.dump(dict(self._commited), f, pickle.HIGHEST_PROTOCOL)

    def _read_file(self):
        '''
        If file self._fname has any content, it is a pickled defaultdict.
        We read and return pickled content, or {}, if file is empty/does not exists.
        '''
        try:
            with open(self._fname, 'rb') as f:
                d = pickle.load(f)
        except (FileNotFoundError, EOFError):
            #   File does not exist, or is empty
            #   -> nothing is stored -> empty dict
            d = {}

        return d
