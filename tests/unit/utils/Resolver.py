# -*- coding: utf-8 -*-
import re

from asyncy.utils import Resolver

import pytest
from pytest import mark

import storyscript


@mark.parametrize('case', [
    ['2 + 2', 4],
    ['0 + 2', 2],
    ['2 / 2', 1],
    ['"a" + "b"', 'ab'],
    ['"a" + "b" + ("c" + "d")', 'abcd'],
    ['2 + 10 / 5', 4],
    ['20 * 100', 2000],
    ['20 / 1000', 0.02],
    ['2 * 4 / 4', 2],
    ['2 * 4 / (4 * 2)', 1],
    ['2 * 4 / (4 * 2) + 1', 2],
    ['2 * 4 / (4 * 2) + 1 * 20', 21],
    ['2 * 4 / (4 * foo) + 1 * 20 + zero', 21, {'foo': 2, 'zero': 0}],
])
def test_resolve_expressions(case):
    # case[0] == the expression under test
    # case[1] == the expected result
    # case[2] == context
    t = storyscript.Api.loads(f'a = {case[0]}')
    context = {}
    if len(case) > 2:
        context = case[2]

    assert case[1] == Resolver.resolve(t['tree']['1']['args'][0], context)


def test_operate_unhandled():
    with pytest.raises(Exception):
        Resolver.operate(1, 1, 'foo')


def test_operate_a_none():
    assert Resolver.operate(None, 1, 'foo') == 1


def test_operate_b_none():
    assert Resolver.operate(1, None, 'foo') == 1


def test_expression_invalid_type():
    with pytest.raises(Exception):
        assert Resolver.expression(
            {'expression': 'a', 'values': [b'asd']}, {}) == 1


@mark.parametrize('cases', [
    [{}, '"yoda"', 'yoda'],
    [{'planet': 'mars'}, 'planet', 'mars'],
    [{'planet': ['mars', 'earth']}, 'planet[0]', 'mars'],
    [{'planet': ['mars', 'earth']}, 'planet[1]', 'earth'],
    [{'planet': {'name': 'mars'}}, 'planet["name"]', 'mars'],
    [{'planet': {'name': 'mars'}}, 'planet["name__"]', None],
    [{'planet': 'mars'}, '{"planet": planet, "element": "air"}',
     {'planet': 'mars', 'element': 'air'}],
    [{}, '[0, 1, 2]', [0, 1, 2]],
    [{}, '/foo/', re.compile('/foo/')],
    [{}, '[true]', [True]],
    [{'i': 1}, 'if i == 1\n  echo foo', True, False],
    [{'i': 2}, 'if i == 1\n  echo foo', False, False],
    [{'i': 2}, 'if i != 1\n  echo foo', True, False],
    [{'i': 1}, 'if i != 1\n  echo foo', False, False],
    [{'i': 5}, 'if i >= 1\n  echo foo', True, False],
    [{'i': 5}, 'if i >= 5\n  echo foo', True, False],
    [{'i': 5}, 'if i >= 6\n  echo foo', False, False],
    [{'i': 5}, 'if i > 5\n  echo foo', False, False],
    [{'i': 5}, 'if i > 4\n  echo foo', True, False],
    [{'i': 5}, 'if i < 5\n  echo foo', False, False],
    [{'i': 5}, 'if i < 6\n  echo foo', True, False],
    [{'i': 5}, 'if i <= 5\n  echo foo', True, False],
    [{'i': 5}, 'if i <= 4\n  echo foo', False, False],
    [{'i': 5}, 'if i <= 6\n  echo foo', True, False],
    [{'i': False}, 'if i\n  echo foo', False, False],
    [{'i': True}, 'if i\n  echo foo', True, False],
    [{'i': True}, 'if !i\n  echo foo', False, False],
    [{'i': False}, 'if !i\n  echo foo', True, False],
    [{'i': None}, 'if !i\n  echo foo', False, False],
])
def test_resolve_all_objects(cases):
    data = cases[0]
    statement = cases[1]
    expected_return = cases[2]
    prepend_var = True
    if len(cases) >= 4:
        prepend_var = cases[3]

    if prepend_var:
        statement = f'a = {statement}'

    tree = storyscript.Api.loads(statement)
    item = tree['tree']['1']['args'][0]

    assert Resolver.resolve(item, data) == expected_return
