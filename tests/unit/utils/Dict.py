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
