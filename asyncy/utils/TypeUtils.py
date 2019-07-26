class TypeUtils:

    @staticmethod
    def isnamedtuple(o):
        t = type(o)
        b = t.__bases__
        if len(b) != 1 or b[0] != tuple:
            return False
        f = getattr(t, '_fields', None)
        if not isinstance(f, tuple):
            return False
        return all(type(n) == str for n in f)
