# -*- coding: utf-8 -*-
import pytest

from storyruntime.utils import Dict


def test_dict_set_single():
    a = {}
    Dict.set(a, ['foobar'], 'string')
    assert a == {'foobar': 'string'}


def test_dict_set_many_new():
    a = {}
    Dict.set(a, ['foo', 'bar'], 'string')
    assert a == {'foo': {'bar': 'string'}}


def test_dict_set_many_old():
    a = {'foo': {'bar': 'data'}}
    Dict.set(a, ['foo', 'bar'], 'string')
    assert a == {'foo': {'bar': 'string'}}


def test_dict_set_many_override():
    a = {'foo': 'string'}
    Dict.set(a, ['foo'], {'bar': 'string'})
    assert a == {'foo': {'bar': 'string'}}


def test_dict_find_simple():
    a = {'foo': 'string'}
    assert Dict.find(a, 'foo') == 'string'


def test_dict_find_deep():
    a = {'foo': {'foo1': {'foo2': 28}}}
    assert Dict.find(a, 'foo.foo1.foo2') == 28


def test_dict_find_object():
    a = {'foo': {'foo1': {}}}
    assert Dict.find(a, 'foo.foo1') == {}


def test_dict_find_root_none():
    assert Dict.find(None, 'foo.foo1') is None
    assert Dict.find(None, 'foo.foo1', 90) == 90


def test_dict_find_missing():
    a = {'foo': {'foo1': {}}}
    assert Dict.find(a, 'foo.foo1.foo2') is None
    assert Dict.find(a, 'foo.foo1.foo2', 900) == 900


def test_dict_find_missing_default_1():
    a = {'foo': {'foo10': {}}}
    assert Dict.find(a, 'foo.foo1', 900) == 900


def test_dict_find_missing_default_2():
    a = {'foo': {'foo1': None}}
    assert Dict.find(a, 'foo.foo1') is None


def test_dict_set_nested():
    a = {
        'a': {'b': {'c': 10}}
    }

    Dict.set(a, ['a', 'b', 'd'], 11)
    assert Dict.find(a, 'a.b.c') == 10
    assert Dict.find(a, 'a.b.d') == 11


def test_dict_set_simple_array():
    a = {
        'a': [1, 2, 3]
    }

    Dict.set(a, ['a', '1'], 11)
    assert a['a'] == [1, 11, 3]


def test_dict_set_nested_array():
    a = {
        'a': {'b': {'c': [1, 2, 3]}}
    }

    Dict.set(a, ['a', 'b', 'c', '0'], 11)
    assert a['a']['b']['c'] == [11, 2, 3]


def test_dict_set_nested_array2():
    a = {
        'a': {
            'b': {
                'c': [{
                    'a1': {
                        'b2': [0, 2, 3]
                    }
                }]
            }
        }
    }

    Dict.set(a, ['a', 'b', 'c', '0', 'a1', 'b2', 0], 11)
    assert a['a']['b']['c'][0]['a1']['b2'] == [11, 2, 3]


def test_dict_set_arrays_in_arrays():
    a = {
        'a': [
            [
                [2], [4, {}]
            ],
            [1],
            [0, 2]
        ]
    }

    Dict.set(a, ['a', '0', '0', '0'], 5)
    Dict.set(a, ['a', '0', '1', '0'], 40)
    Dict.set(a, ['a', '0', '1', '1', 'a'], 'c')
    assert a == {
        'a': [
            [
                [5], [40, {'a': 'c'}]
            ],
            [1],
            [0, 2]
        ]
    }


def test_dict_set_array_out_of_bounds():
    a = {
        'a': []
    }

    with pytest.raises(IndexError):
        Dict.set(a, ['a', '0'], 'foo')
