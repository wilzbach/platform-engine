# -*- coding: utf-8 -*-
import random

from ..Exceptions import AsyncyError


class Mutations:

    @classmethod
    def list_shift(cls, l, n):
        return l[n:] + l[:n]

    @classmethod
    def _mutate_string(cls, mutation, value, story, operator):
        operand = story.argument_by_name(mutation, operator)
        if operator == 'length':
            return len(value)
        elif operator == 'replace':
            new_val = story.argument_by_name(mutation, 'with')
            return value.replace(operand, new_val)
        elif operator == 'split':
            return value.split(operand)
        elif operator == 'uppercase':
            return value.upper()
        elif operator == 'lowercase':
            return value.lower()

    @classmethod
    def _mutate_list(cls, mutation, value, story, operator):
        operand = story.argument_by_name(mutation, operator)
        if operator == 'index':
            try:
                return value.index(operand)
            except ValueError:
                return -1
        elif operator == 'length':
            return len(value)
        elif operator == 'join':
            return operand.join(value)
        elif operator == 'random':
            return random.choice(value)
        elif operator == 'reverse':
            value.reverse()
            return
        elif operator == 'shift':
            if operand == 'left':
                return cls.list_shift(value, -1)
            elif operand == 'right':
                return cls.list_shift(value, 1)
        elif operator == 'sort':
            value.sort()
            return
        elif operator == 'min':
            return min(value)
        elif operator == 'max':
            return max(value)
        elif operator == 'sum':
            return sum(value)
        elif operator == 'contains':
            if operand in value:
                return True
            return False
        elif operator == 'add':
            value.append(operand)
            return
        elif operator == 'remove':
            try:
                value.remove(operand)
            except ValueError:
                # The value to be removed is not in the list.
                pass
            return

    @classmethod
    def _mutate_dict(cls, mutation, value, story, operator):
        operand = story.argument_by_name(mutation, operator)
        if operator == 'size':
            return len(value)
        elif operator == 'keys':
            return list(value.keys())
        elif operator == 'values':
            return list(value.values())
        elif operator == 'items':
            value.items()
            # TODO
            pass
        elif operator == 'pop':
            return value.pop(operand, None)
        elif operator == 'get':
            return value.get(operand)
        elif operator == 'has':
            return value.get(operand) is not None

    @classmethod
    def _mutate_numbers(cls, mutation, value, story, operator):
        operand = story.argument_by_name(mutation, operator)
        if operator == 'is_odd':
            return value % 2 == 1
        elif operator == 'is_even':
            return value % 2 == 0
        elif operator == 'absolute':
            return abs(value)
        elif operator == 'decrement':
            return value - 1
        elif operator == 'increment':
            return value + 1
        elif operator == '+':
            return value + operand
        elif operator == '-':
            return value - operand
        elif operator == '/':
            return value / operand
        elif operator == '*':
            return value * operand
        elif operator == '^':
            return pow(value, operand)

    @classmethod
    def mutate(cls, mutation, value, story, line):
        operator = mutation['mutation']
        if isinstance(value, str):
            return cls._mutate_string(mutation, value, story, operator)
        elif isinstance(value, list):
            return cls._mutate_list(mutation, value, story, operator)
        elif isinstance(value, dict):
            return cls._mutate_dict(mutation, value, story, operator)
        elif isinstance(value, int) or isinstance(value, float):
            return cls._mutate_numbers(mutation, value, story, operator)

        raise AsyncyError(
            message=f'Unsupported data type {str(type(value))} '
                    f'for mutation {operator}',
            story=story, line=line)
