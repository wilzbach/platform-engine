# -*- coding: utf-8 -*-
from asyncy.utils import Dict


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
    Dict.set(a, ['foo', 'bar'], 'string')
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
