# -*- coding: utf-8 -*-
import re

from .TypeResolver import TypeResolver
from .TypeUtils import TypeUtils
from ..Exceptions import StoryscriptRuntimeError


class Resolver:

    def __init__(self, story):
        self.story = story

    def values(self, items_list):
        """
        Parses a list of values objects. The list may contain other objects.
        """
        return [
            self.resolve(value)
            for value in items_list
        ]

    def string(self, string, values=None):
        """
        Resolves a string to itself. If values are given, the string
        is formatted against data, using the order in values.
        """
        if values:
            values = self.values(values)
            return string.format(*values)
        return string

    def path(self, paths):
        """
        Resolves a path against some data, for example the path ['a', 'b']
        with data {'a': {'b': 'value'}} produces 'value'
        """
        resolved = None
        try:
            data = self.story.resolve_context(paths[0])
            item = data[paths[0]]
            for path in paths[1:]:
                if isinstance(path, str):
                    item = item[path]

                assert isinstance(path, dict)
                object_type = path.get('$OBJECT')
                if object_type == 'range':
                    item = self.range(path['range'], item)
                else:
                    resolved = self.object(path)
                    # Allow a namedtuple to use keys or index
                    # to retrieve data.
                    if TypeUtils.isnamedtuple(item) and \
                            isinstance(resolved, str):
                        item = getattr(item, resolved)
                    else:
                        item = item[resolved]
            return item
        except IndexError:
            raise StoryscriptRuntimeError(
                message=f'List index out of bounds: {resolved}')
        except (KeyError, AttributeError):
            raise StoryscriptRuntimeError(
                message=f'Map does not contain the key "{resolved}". '
                f'Use map.get(key: <key> default: <default value>) to '
                f'prevent an exception from being thrown. Additionally, you '
                f'may also use map.contains(key: <key>) to check if a key '
                f'exists in a map.')
        except TypeError:
            return None

    def dictionary(self, dictionary):
        result = {}
        for key, value in dictionary.items():
            result[key] = self.resolve(value)
        return result

    def list_object(self, items):
        for item in items:
            yield self.resolve(item)

    def object(self, item):
        if not isinstance(item, dict):
            return item
        object_type = item.get('$OBJECT')
        if object_type == 'string':
            if 'values' in item:
                return self.string(item['string'], values=item['values'])
            return self.string(item['string'])
        elif object_type == 'dot':
            return item['dot']
        elif object_type == 'int':
            return item['int']
        elif object_type == 'time':
            return item['ms']
        elif object_type == 'boolean':
            return item['boolean']
        elif object_type == 'float':
            return item['float']
        elif object_type == 'path':
            return self.path(item['paths'])
        elif object_type == 'regexp':
            return re.compile(item['regexp'])
        elif object_type == 'value':
            return item['value']
        elif object_type == 'dict':
            return dict(self.dict(item['items']))
        elif object_type == 'list':
            return list(self.list_object(item['items']))
        elif object_type == 'expression' or object_type == 'assertion':
            return self.expression(item)
        elif object_type == 'type_cast':
            return self.type_cast(item)
        elif object_type == 'type':
            return self.type_cast(item)
        return self.dictionary(item)

    def expression(self, item):
        """
        Handles expression where item['assertion'/'expression']
        is one of the following:
        - equals
        - not_equal
        - greater
        - greater_equal
        - less
        - less_equal
        - not
        - or
        - sum
        - subtraction
        - division
        - multiplication
        - exponential
        """
        a = item.get('assertion', item.get('expression'))

        values = item['values']

        left = self.resolve(values[0])

        if a == 'equals' or a == 'equal':
            right = self.resolve(values[1])
            return left == right
        elif a == 'not_equal':
            right = self.resolve(values[1])
            return left != right
        elif a == 'greater':
            right = self.resolve(values[1])
            return left > right
        elif a == 'greater_equal':
            right = self.resolve(values[1])
            return left >= right
        elif a == 'less':
            right = self.resolve(values[1])
            return left < right
        elif a == 'less_equal':
            right = self.resolve(values[1])
            return left <= right
        elif a == 'not':
            return not left
        elif a == 'or':
            if left is True:
                return True

            for i in range(1, len(values)):
                result = self.resolve(values[i])
                if result is True:
                    return True

            return False
        elif a == 'and':
            if left is False:
                return False

            for i in range(1, len(values)):
                result = self.resolve(values[i])
                if result is False:
                    return False

            return True
        elif a == 'sum':
            result = left

            assert type(left) in (int, float, str)
            # Sum supports flattened values since this only occurs when
            # a string like "{a} {b} {c}" is compiled. Everything else,
            # including arithmetic is compiled as a nested expression.
            for i in range(1, len(values)):
                r = self.resolve(values[i])

                if type(r) in (int, float) and type(result) in (int, float):
                    result += r
                else:
                    result = f'{str(result)}{str(r)}'

            return result
        elif a == 'subtraction':
            right = self.resolve(values[1])
            assert type(left) in (int, float)
            assert type(right) in (int, float)
            return left - right
        elif a == 'multiplication':
            right = self.resolve(values[1])
            assert type(left) in (int, float, str)
            assert type(right) in (int, float, str)
            return left * right
        elif a == 'modulus':
            right = self.resolve(values[1])
            assert type(left) in (int, float)
            assert type(right) in (int, float)
            return left % right
        elif a == 'division':
            right = self.resolve(values[1])
            assert type(left) in (int, float, str)
            assert type(right) in (int, float, str)
            return left / right
        elif a == 'exponential':
            right = self.resolve(values[1])
            assert type(left) in (int, float)
            assert type(right) in (int, float)
            return left ** right
        else:
            assert False, f'Unsupported operation: {a}'

    def dict(self, items):
        for k, v in items:
            k = self.object(k)
            if k in (list, tuple, dict):
                # warn or raise?
                pass
            else:
                yield k, self.object(v)

    def list(self, items):
        result = []
        for item in items:
            result.append(self.resolve(item))
        return ' '.join(result)

    def type_cast(self, item):
        type_ = item['type']
        item = self.object(item['value'])
        return TypeResolver.type_cast(item, type_)

    def range(self, path, item):
        start = 0
        end = len(item)
        if 'start' in path:
            start = self.object(path['start'])
        if 'end' in path:
            end = self.object(path['end'])
        return item[start:end]

    def resolve(self, item):
        # Sanitize this item so we can ensure that
        # any unwanted data doesn't leak.
        item = TypeUtils.safe_type(item)
        if type(item) is dict:
            return self.object(item)
        elif type(item) is list:
            return self.list(item)
        return item
