# -*- coding: utf-8 -*-


class StringMutations:

    @classmethod
    def _list_shift(cls, l, n):
        return l[n:] + l[:n]

    @classmethod
    def length(cls, mutation, value, story, operator, operand):
        return len(value)

    @classmethod
    def replace(cls, mutation, value, story, operator, operand):
        new_val = story.argument_by_name(mutation, 'with')
        return value.replace(operand, new_val)

    @classmethod
    def split(cls, mutation, value, story, operator, operand):
        return value.split(operand)

    @classmethod
    def uppercase(cls, mutation, value, story, operator, operand):
        return value.upper()

    @classmethod
    def lowercase(cls, mutation, value, story, operator, operand):
        return value.lower()
