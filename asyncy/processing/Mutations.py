# -*- coding: utf-8 -*-
from .mutations.DictMutations import DictMutations
from .mutations.ListMutations import ListMutations
from .mutations.NumberMutations import NumberMutations
from .mutations.StringMutations import StringMutations
from ..Exceptions import AsyncyError


class Mutations:

    @classmethod
    def mutate(cls, mutation, value, story, line):
        operator = mutation['mutation']
        operand = story.argument_by_name(mutation, operator)
        handler = None
        try:
            if isinstance(value, str):
                handler = getattr(StringMutations, operator)
            elif isinstance(value, list):
                handler = getattr(ListMutations, operator)
            elif isinstance(value, dict):
                handler = getattr(DictMutations, operator)
            elif isinstance(value, int) or isinstance(value, float):
                if operator in ['+', '-', '/', '^', '*']:
                    handler = NumberMutations.op_unary
                else:
                    handler = getattr(NumberMutations, operator)
        except AttributeError:
            pass  # handler is None at this point.

        if handler is None:
            raise AsyncyError(
                message=f'Unsupported data type {str(type(value))} '
                        f'for mutation {operator}',
                story=story, line=line)

        return handler(mutation, value, story, operator, operand)
