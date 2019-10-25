# -*- coding: utf-8 -*-
import pytest

from storyruntime.utils.ConstDict import ConstDict


@pytest.fixture
def regular_dict():
    return {"a": 1, "b": 2, "c": 3}


@pytest.fixture
def const_dict(regular_dict):
    return ConstDict(regular_dict)


def test_getattr(regular_dict, const_dict):
    assert const_dict.a == regular_dict["a"]
    assert const_dict.b == regular_dict["b"]
    assert const_dict.c == regular_dict["c"]


def test_getitem(regular_dict, const_dict):
    for key, value in regular_dict.items():
        assert const_dict[key] == value


def test_setattr(const_dict):
    with pytest.raises(Exception):
        const_dict.a = 0


def test_setitem(const_dict):
    with pytest.raises(Exception):
        const_dict["a"] = 0


def test_keys(regular_dict, const_dict):
    assert const_dict.keys() == regular_dict.keys()


def test_items(regular_dict, const_dict):
    assert const_dict.items() == regular_dict.items()


def test_contains(const_dict):
    assert ("a" in const_dict) is True
    assert ("x" in const_dict) is False
