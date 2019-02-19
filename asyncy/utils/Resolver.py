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
        except (KeyError, TypeError, IndexError):
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
        if not isinstance(item, dict):
            return item
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
        elif object_type == 'expression':
            return cls.expression(item, data)
        elif object_type == 'assertion':
            return cls.assertion(item, data)
        return cls.dictionary(item, data)

    @classmethod
    def operate(cls, a, b, expression):
        if a is None:
            return b
        elif b is None:
            return a
        elif expression == 'sum':
            return a + b
        elif expression == 'multiplication':
            return a * b
        elif expression == 'division':
            return a / b
        else:
            raise Exception(f'Unhandled expression {expression}!')

    @classmethod
    def expression(cls, item, data):
        result = None
        expression = item['expression']
        for val in item['values']:
            if isinstance(val, dict):
                val = cls.resolve(val, data)

            if type(val) in (int, float, str):
                result = cls.operate(result, val, expression)
            else:
                raise Exception(f'Cannot operate on type {str(type(val))}! '
                                f'Must be one of int, float, str')

        return result

    @classmethod
    def assertion(cls, item, data):
        """
        Handles assertions where item['assertion'] is one of the following:
        - equals
        - not_equal
        - greater
        - greater_equal
        - less
        - less_equal
        - not
        """
        a = item['assertion']
        values = item['values']
        assert len(values) <= 2, \
            f'Only simple assertions are supported. Found {len(values)}'

        left = cls.resolve(values[0], data)
        right = None

        if len(values) == 2:
            right = cls.resolve(values[1], data)

        if a == 'equals':
            return left == right
        elif a == 'not_equal':
            return left != right
        elif a == 'greater':
            return left > right
        elif a == 'greater_equal':
            return left >= right
        elif a == 'less':
            return left < right
        elif a == 'less_equal':
            return left <= right
        elif a == 'not':
            return left is False
        else:
            assert False, f'Unsupported operation: {a}'

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
        return ' '.join(result)

    @classmethod
    def resolve(cls, item, data):
        if type(item) is dict:
            return cls.object(item, data)
        elif type(item) is list:
            return cls.list(item, data)
        return item
