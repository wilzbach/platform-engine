# -*- coding: utf-8 -*-


class Dict:

    @staticmethod
    def set(_dict, keys, output):
        if len(keys) == 1:
            _dict[keys[0]] = output
        else:
            _cur = _dict
            intermediate, last = keys[:-1], keys[-1]
            for key in intermediate:
                if isinstance(_cur, list):
                    _cur = _cur[key]
                else:
                    _cur = _cur.setdefault(key, {})
            _cur[last] = output

    @staticmethod
    def find(root, path, default_value=None):
        """
        Finds a nested value in `root` by splitting `path` by a `.`.

        :param default_value: If the value is not found, return this value
        :param root: The dictionary to scan through
        :param path: The path to the value, eg "foo.bar.a.b.v"
        :return: The value, if found, `default_value` if not found
        """
        if root is None or path is None:
            return default_value

        assert isinstance(path, str)
        tokens = path.split('.')
        for token in tokens:
            root = root.get(token)
            if root is None:
                return default_value

        return root
