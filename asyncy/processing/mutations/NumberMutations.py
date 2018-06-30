# -*- coding: utf-8 -*-


class NumberMutations:

    @classmethod
    def op_unary(cls, mutation, value, story, operator, operand):
        if operator == '*':
            return value * operand
        elif operator == '/':
            return value / operand
        elif operator == '+':
            return value + operand
        elif operator == '-':
            return value - operand
        elif operator == '^':
            return pow(value, operand)

    @classmethod
    def is_odd(cls, mutation, value, story, operator, operand):
        return value % 2 == 1

    @classmethod
    def is_even(cls, mutation, value, story, operator, operand):
        return value % 2 == 0

    @classmethod
    def absolute(cls, mutation, value, story, operator, operand):
        return abs(value)

    @classmethod
    def decrement(cls, mutation, value, story, operator, operand):
        return value - 1

    @classmethod
    def increment(cls, mutation, value, story, operator, operand):
        return value + 1
