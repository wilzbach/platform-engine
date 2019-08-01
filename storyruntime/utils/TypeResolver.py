# -*- coding: utf-8 -*-
import re

import storyscript.compiler.semantics.types.Types as types

from ..Exceptions import TypeAssertionRuntimeError, TypeValueRuntimeError


# Python 3.6: _sre.SRE_Pattern
# Python 3.7: re.Pattern
RE_PATTERN = type(re.compile('a'))


class TypeAssertionError(Exception):
    """
    Raised when runtime type can't be converted.
    """
    pass


class TypeResolver:

    @classmethod
    def resolve_type(cls, item):
        assert isinstance(item, dict)
        object_type = item.get('type')
        if object_type == 'List':
            return types.ListType(cls.resolve_type(item['values'][0]))
        elif object_type == 'Map':
            values = item['values']
            assert len(values) == 2
            key = cls.resolve_type(values[0])
            value = cls.resolve_type(values[1])
            return types.MapType(key, value)
        elif object_type == 'any':
            return types.AnyType.instance()
        elif object_type == 'regex':
            return types.RegExpType.instance()
        elif object_type == 'boolean':
            return types.BooleanType.instance()
        elif object_type == 'int':
            return types.IntType.instance()
        elif object_type == 'float':
            return types.FloatType.instance()
        else:
            assert object_type == 'string'
            return types.StringType.instance()

    @staticmethod
    def assert_type(expected, item):
        for t in expected:
            if isinstance(item, t):
                return
        raise TypeAssertionError()

    @classmethod
    def type_string(cls, item):
        if isinstance(item, list):
            inner = 'any'
            if len(item) > 0:
                inner = cls.type_string(item[0])
            return f'List[{inner}]'
        elif isinstance(item, dict):
            key = 'any'
            value = 'any'
            if len(item) > 0:
                k, v = next(iter(item.items()))
                key = cls.type_string(k)
                value = cls.type_string(v)
            return f'Map[{key},{value}]'
        elif isinstance(item, bool):
            return 'boolean'
        elif isinstance(item, int):
            return 'int'
        elif isinstance(item, float):
            return 'float'
        elif isinstance(item, str):
            return 'str'
        elif isinstance(item, RE_PATTERN):
            return 'regexp'
        else:
            return f'unknown type {type(item)}'

    @classmethod
    def check_type_cast(cls, type_exp, item):
        if item is None:
            return None
        elif isinstance(type_exp, types.ListType):
            cls.assert_type([list], item)
            li = []
            for el in item:
                li.append(cls.check_type_cast(type_exp.inner, el))
            return li
        elif isinstance(type_exp, types.MapType):
            cls.assert_type([dict], item)
            obj = {}
            for k, v in item.items():
                key = cls.check_type_cast(type_exp.key, k)
                value = cls.check_type_cast(type_exp.value, v)
                obj[key] = value
            return obj
        elif isinstance(type_exp, types.BooleanType):
            return bool(item)
        elif isinstance(type_exp, types.IntType):
            return int(item)
        elif isinstance(type_exp, types.FloatType):
            return float(item)
        elif isinstance(type_exp, types.StringType):
            return str(item)
        elif isinstance(type_exp, types.AnyType):
            return item
        else:
            assert isinstance(type_exp, types.RegExpType)
            cls.assert_type([str, RE_PATTERN], item)
            if isinstance(item, str):
                return re.compile(item)
            return item

    @staticmethod
    def item_to_string(item):
        """
        Stringifies an item.
        """
        if isinstance(item, RE_PATTERN):
            return f'/{item.pattern}/'
        return str(item)

    @classmethod
    def type_cast(cls, item, type_, data):
        t = cls.resolve_type(type_)
        value = cls.item_to_string(item)
        type_received = cls.type_string(item)
        try:
            return cls.check_type_cast(t, item)
        except (TypeError, TypeAssertionError):
            raise TypeAssertionRuntimeError(type_expected=t,
                                            type_received=type_received,
                                            value=value)
        except (ValueError, re.error):
            raise TypeValueRuntimeError(type_expected=t,
                                        type_received=type_received,
                                        value=value)
