# -*- coding: utf-8 -*-


class NumberMutations:

    @classmethod
    def op_unary(cls, mutation, value, story, line, operator, operand):
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
    def is_odd(cls, mutation, value, story, line, operator, operand):
        return value % 2 == 1

    @classmethod
    def is_even(cls, mutation, value, story, line, operator, operand):
        return value % 2 == 0

    @classmethod
    def absolute(cls, mutation, value, story, line, operator, operand):
        return abs(value)

    @classmethod
    def decrement(cls, mutation, value, story, line, operator, operand):
        result = value - 1
        cls._update_path(story, line, result)
        return result

    @classmethod
    def _update_path(cls, story, line, result):
        """
        Updates the LHS of the operator. This is used by increment/decrement.
        Consider the following cases:
        1. a increment
        2. b = a increment
        3. b = 10 increment
        4. a = a increment

        In cases 1 and 4, a must be 11, if a was 10 previously.
        In case 2, b and a must be both 11, if a was 10 previously.
        In case 3, b is 11.
        """
        if len(line['args']) == 2 and type(line['args'][0]) is dict:
            story.set_variable(assign=line['args'][0], output=result)
        elif len(line['args']) == 3 and type(line['args'][1]) is dict:
            story.set_variable(assign=line['args'][1], output=result)

    @classmethod
    def increment(cls, mutation, value, story, line, operator, operand):
        result = value + 1
        cls._update_path(story, line, result)
        return result
