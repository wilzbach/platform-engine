# -*- coding: utf-8 -*-


class IntegerMutations:
    @classmethod
    def isOdd(cls, mutation, value, story, line, operator):
        return value % 2 == 1

    @classmethod
    def isEven(cls, mutation, value, story, line, operator):
        return value % 2 == 0

    @classmethod
    def absolute(cls, mutation, value, story, line, operator):
        return abs(value)

    @classmethod
    def decrement(cls, mutation, value, story, line, operator):
        return value - 1

    @classmethod
    def increment(cls, mutation, value, story, line, operator):
        return value + 1
