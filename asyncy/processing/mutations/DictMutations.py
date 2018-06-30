# -*- coding: utf-8 -*-


class DictMutations:

    @classmethod
    def size(cls, mutation, value, story, operator, operand):
        return len(value)

    @classmethod
    def keys(cls, mutation, value, story, operator, operand):
        return list(value.keys())

    @classmethod
    def values(cls, mutation, value, story, operator, operand):
        return list(value.values())

    @classmethod
    def pop(cls, mutation, value, story, operator, operand):
        return value.pop(operand, None)

    @classmethod
    def get(cls, mutation, value, story, operator, operand):
        return value.get(operand)

    @classmethod
    def has(cls, mutation, value, story, operator, operand):
        return value.get(operand) is not None
