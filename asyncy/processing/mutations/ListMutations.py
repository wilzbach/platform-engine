# -*- coding: utf-8 -*-
import random


class ListMutations:

    @classmethod
    def _list_shift(cls, l, n):
        return l[n:] + l[:n]

    @classmethod
    def index(cls, mutation, value, story, operator, operand):
        try:
            return value.index(operand)
        except ValueError:
            return -1

    @classmethod
    def length(cls, mutation, value, story, operator, operand):
        return len(value)

    @classmethod
    def join(cls, mutation, value, story, operator, operand):
        return operand.join(value)

    @classmethod
    def random(cls, mutation, value, story, operator, operand):
        return random.choice(value)

    @classmethod
    def reverse(cls, mutation, value, story, operator, operand):
        value.reverse()

    @classmethod
    def shift(cls, mutation, value, story, operator, operand):
        shifted = value
        if operand == 'left':
            shifted = cls._list_shift(value, 1)
        elif operand == 'right':
            shifted = cls._list_shift(value, -1)

        # Copy the values of shifted into the original value.
        # This is because our impl of shift is inplace.
        for i in range(0, len(value)):
            value[i] = shifted[i]

    @classmethod
    def sort(cls, mutation, value, story, operator, operand):
        value.sort()

    @classmethod
    def min(cls, mutation, value, story, operator, operand):
        return min(value)

    @classmethod
    def max(cls, mutation, value, story, operator, operand):
        return max(value)

    @classmethod
    def sum(cls, mutation, value, story, operator, operand):
        return sum(value)

    @classmethod
    def contains(cls, mutation, value, story, operator, operand):
        return operand in value

    @classmethod
    def add(cls, mutation, value, story, operator, operand):
        value.append(operand)

    @classmethod
    def remove(cls, mutation, value, story, operator, operand):
        try:
            value.remove(operand)
        except ValueError:
            # The value to be removed is not in the list.
            pass
