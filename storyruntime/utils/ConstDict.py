class ConstDict:
    """
    Like a dict, but with constant attributes.
    """

    def __init__(self, data):
        object.__setattr__(self, "_data", data)

    def __getattr__(self, attr):
        return self._data[attr]

    def __setattr__(self, key, value):
        raise TypeError("'ConstDict' object is readonly")

    def __getitem__(self, item):
        return self._data[item]

    def __contains__(self, item):
        return item in self._data

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()
