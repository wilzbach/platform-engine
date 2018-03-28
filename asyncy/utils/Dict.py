# -*- coding: utf-8 -*-


class Dict:

    @staticmethod
    def set(_dict, keys, output):
        if len(keys) == 1:
            _dict[keys[0]] = output
        else:
            _cur = _dict
            last = keys.pop()
            for key in keys:
                _cur = _cur.setdefault(key, {})
                if not isinstance(_cur, dict):
                    _dict[key] = {}
                    _cur = _dict[key]
            _cur[last] = output
