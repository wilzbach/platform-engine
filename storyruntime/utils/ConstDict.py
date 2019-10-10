class ConstDict:
    """
    Like a dict, but with constant attributes.
    """

    def __init__(self, data):
        self._data = data

    def __getattr__(self, attr):
        return self._data[attr]

    def __getitem__(self, item):
        return self._data[item]

    def keys(self):
        return self._data.keys()
