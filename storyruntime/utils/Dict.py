# -*- coding: utf-8 -*-
from .Resolver import Resolver


class Dict:

    @staticmethod
    def set(_dict, keys, output):
        if len(keys) == 1:
            _dict[keys[0]] = output
        else:
            _cur = _dict
            last = keys.pop()
            for key in keys:
                if isinstance(_cur, list):
                    _cur = _cur[Dict.parse_int(key)]
                else:
                    _cur = _cur.setdefault(key, {})

            if isinstance(_cur, list):
                _cur[Dict.parse_int(last)] = output
            else:
                _cur[Dict.parse_map_key(last, _dict)] = output

    @staticmethod
    def parse_int(s):
        if isinstance(s, str):
            # backwards-compatibility
            return int(s)
        elif isinstance(s, int):
            # general purpose dict
            # ss output will never hit this branch
            return s
        elif isinstance(s, dict) and s.get('$OBJECT') == 'int':
            return s['int']
        else:
            raise Exception(f'Unable to parse {type(s)} as int.')

    @staticmethod
    def parse_map_key(item, context):
        if isinstance(item, dict):
            object_type = item.get('$OBJECT')
            if object_type == 'string':
                return item['string']
            elif object_type == 'int':
                return item['int']
            elif object_type == 'float':
                return item['float']
            elif object_type == 'path':
                return Resolver.path(item['paths'], context)
        elif isinstance(item, str) and item.lstrip('+-').isdigit():
            # backwards-compatibility
            return int(item)
        else:
            # general purpose dict
            # ss output will never hit this branch
            return item

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
