# -*- coding: utf-8 -*-
import re
from functools import reduce


class Resolver:

    @staticmethod
    def _walk(item, index):
        if isinstance(index, dict):
            return item[Resolver.object(index, item)]
        elif index.isdigit():
            return item[int(index)]
        return item[index]

    @classmethod
    def values(cls, items_list, data):
        """
        Parses a list of values objects. The list may contain other objects.
        """
        return [
            Resolver.resolve(value, data)
            for value in items_list
        ]

    @classmethod
    def string(cls, string, data, values=None):
        """
        Resolves a string to itself. If values are given, the string
        is formatted against data, using the order in values.
        """
        if values:
            values = Resolver.values(values, data)
            return string.format(*values)
        return string

    @classmethod
    def path(cls, paths, data):
        """
        Resolves a path against some data, for example the path ['a', 'b']
        with data {'a': {'b': 'value'}} produces 'value'
        """
        try:
            return reduce(cls._walk, paths, data)
        except (KeyError, TypeError):
            return None

    @classmethod
    def dictionary(cls, dictionary, data):
        result = {}
        for key, value in dictionary.items():
            result[key] = cls.resolve(value, data)
        return result

    @classmethod
    def list_object(cls, items, data):
        for item in items:
            yield cls.resolve(item, data)

    @classmethod
    def object(cls, item, data):
        object_type = item.get('$OBJECT')
        if object_type == 'string':
            if 'values' in item:
                return cls.string(item['string'], data, values=item['values'])
            return cls.string(item['string'], data)
        elif object_type == 'path':
            return cls.path(item['paths'], data)
        elif object_type == 'regexp':
            return re.compile(item['regexp'])
        elif object_type == 'value':
            return item['value']
        elif object_type == 'dict':
            return dict(cls.dict(item['items'], data))
        elif object_type == 'list':
            return list(cls.list_object(item['items'], data))
        return cls.dictionary(item, data)

    @classmethod
    def dict(cls, items, data):
        for k, v in items:
            k = cls.object(k, data)
            if k in (list, tuple, dict):
                # warn or raise?
                pass
            else:
                yield k, cls.object(v, data)

    @classmethod
    def list(cls, items, data):
        result = []
        for item in items:
            result.append(cls.resolve(item, data))
        if len(result) == 1:
            if type(result[0]) is bool:
                return result
        return ' '.join(result)

    @classmethod
    def resolve(cls, item, data):
        if type(item) is dict:
            return cls.object(item, data)
        elif type(item) is list:
            return cls.list(item, data)
        return item
