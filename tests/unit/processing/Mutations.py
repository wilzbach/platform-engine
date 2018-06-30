# -*- coding: utf-8 -*-
from asyncy.Exceptions import AsyncyError
from asyncy.processing.Mutations import Mutations

import pytest
from pytest import mark


@mark.parametrize('case', [
    # Protocol for a case:
    # case[0] = value (LHS operand)
    # case[1] = operator (mutation)
    # case[2] = operand (RHS operand. If not required, pass None)
    # case[3] = expected return type
    # case[4] = inplace (True if case[0] changes - inplace update)

    # --- BEGIN - list ---
    [['a', 's', 'y', 'n', 'c', 'y'], 'index', 's', 1, False],
    [['a', 's', 'y', 'n', 'c', 'y'], 'index', 'z', -1, False],
    [['a', 's', 'y', 'n', 'c', 'y'], 'length', None, 6, False],
    [['a', 's', 'y', 'n', 'c', 'y'], 'join', '', 'asyncy', False],
    [['a', 's', 'y', 'n', 'c', 'y'], 'join', ':', 'a:s:y:n:c:y', False],
    [['f', 'o', 'o'], 'reverse', None, ['o', 'o', 'f'], True],
    [['f', 'o', 'o'], 'shift', 'left', ['o', 'o', 'f'], True],
    [['f', 'o', 'o'], 'shift', 'right', ['o', 'f', 'o'], True],
    [[9, 8, 2, 1, 10], 'sort', None, [1, 2, 8, 9, 10], True],
    [[9, 8, 2, 1, 10], 'min', None, 1, False],
    [[9, 8, 2, 1, 10], 'max', None, 10, False],
    [[9, 8, 2, 1, 10], 'sum', None, 30, False],
    [[9, 8, 2, 1, 10], 'contains', 10, True, False],
    [[9, 8, 2, 1, 10], 'contains', 18828, False, False],
    [[9, 8, 2, 1, 10], 'add', 20, [9, 8, 2, 1, 10, 20], True],
    [[9, 8, 2, 1, 10], 'remove', 9, [8, 2, 1, 10], True],
    [[9, 8, 2, 1, 10], 'remove', 9999, [9, 8, 2, 1, 10], True],
    # --- END - list ---

    # --- BEGIN - string ---
    ['asyncy', 'length', None, 6, False],
    ['asy|ncy', 'split', '|', ['asy', 'ncy'], False],
    ['asyncY', 'uppercase', None, 'ASYNCY', False],
    ['asYnCy', 'lowercase', None, 'asyncy', False],
    # --- END - string ---

    # --- BEGIN - numbers ---
    [10, 'is_odd', None, False, False],
    [9, 'is_odd', None, True, False],
    [10, 'is_even', None, True, False],
    [9, 'is_even', None, False, False],
    [-10, 'absolute', None, 10, False],
    [10, 'absolute', None, 10, False],
    [10, 'decrement', None, 9, False],
    [0, 'decrement', None, -1, False],
    [-1, 'increment', None, 0, False],
    [10, 'increment', None, 11, False],
    [10, '+', 10, 20, False],
    [10, '+', -10, 0, False],
    [10, '-', 5, 5, False],
    [10, '-', -5, 15, False],
    [10, '/', 5, 2, False],
    [10, '*', 7, 70, False],
    [10, '*', -7, -70, False],
    [2, '^', 10, 1024, False],
    # --- END - numbers ---

    # --- BEGIN - dict ---
    [{'a': '1', 'b': 2}, 'size', None, 2, False],
    [{'a': '1', 'b': 2}, 'keys', None, ['a', 'b'], False],
    [{'a': '1', 'b': 2}, 'values', None, ['1', 2], False],
    [{'a': '1', 'b': 2}, 'get', 'a', '1', False],
    [{'a': '1', 'b': 2}, 'get', 'x', None, False],
    [{'a': '1', 'b': 2}, 'has', 'a', True, False],
    [{'a': '1', 'b': 2}, 'has', 'x', False, False],
    # --- END - dict ---
])
def test_mutations_mutate(story, case):
    story.context = {}
    mutation = {
        '$OBJECT': 'mutation',
        'mutation': case[1],
        'args': [
            {
                '$OBJECT': 'argument',
                'name': case[1],
                'argument': {
                    '$OBJECT': 'string',
                    'string': case[2]
                }
            }
        ]
    }

    line = {
        'args': [
            {
                'paths': ['my_var']
            },
            'value',
            mutation
        ]
    }

    if case[4]:
        # Inplace updates.
        assert Mutations.mutate(mutation, case[0], story, line) is None
        assert case[0] == case[3]
    else:
        # Check return type.
        assert Mutations.mutate(mutation, case[0], story, line) == case[3]


def test_mutations_string_replace(story):
    mutation = {
        'mutation': 'replace',
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'replace',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'y'
                }
            },
            {
                '$OBJECT': 'argument',
                'name': 'with',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'Y'
                }
            }
        ]
    }

    assert Mutations.mutate(mutation, 'asyncy', story, None) == 'asYncY'


def test_mutations_string_random(story):
    mutation = {
        'mutation': 'random'
    }

    options = [28, 12, 8, 1]

    for i in range(0, 10):
        choice = Mutations.mutate(mutation, options, story, None)
        assert choice in options


def test_mutations_string_pop(story):
    mutation = {
        'mutation': 'pop',
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'pop',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'y'
                }
            }
        ]
    }

    value = {'a': 1, 'y': 2}
    assert Mutations.mutate(mutation, value, story, None) == 2
    assert Mutations.mutate(mutation, value, story, None) is None


def test_mutations_unexpected_type(story):
    mutation = {
        'mutation': 'foo'
    }

    with pytest.raises(AsyncyError):
        Mutations.mutate(mutation, Mutations, story, None)


def test_mutations_unexpected_mutation(story):
    mutation = {
        'mutation': 'foo'
    }

    with pytest.raises(AsyncyError):
        Mutations.mutate(mutation, 'string', story, None)


@mark.parametrize('op', [['increment', 1], ['decrement', -1]])
def test_mutation_int_ops(story, op):
    story.context = {'foo': 10}
    mutation = {
        '$OBJECT': 'mutation',
        'mutation': op[0],
        'args': [
            {
                '$OBJECT': 'argument',
                'name': op[0],
                'argument': {
                    '$OBJECT': 'number',
                    'number': 10
                }
            }
        ]
    }

    line = {
        'args': [
            {
                'paths': ['foo']
            },
            {'paths': ['foo']},
            mutation
        ]
    }

    # To test a case where len(args) is 2, for example, `a increment`
    # len(args) is 3 when the statement is `a = a increment`
    if op[0] == 'increment':
        line['args'].pop(0)

    assert story.context['foo'] == 10
    assert Mutations.mutate(mutation, 10, story, line) == 10 + op[1]
    assert story.context['foo'] == 10 + op[1]
