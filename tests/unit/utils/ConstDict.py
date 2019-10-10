# -*- coding: utf-8 -*-
import pytest

from storyruntime.utils.ConstDict import ConstDict


def test_is_const():
    normal_dict = {
        'a': 1,
        'b': 2,
        'c': 3
    }
    const_dict = ConstDict({
        'a': 1,
        'b': 2,
        'c': 3
    })
    # getattr
    assert const_dict.a == normal_dict['a']
    assert const_dict.b == normal_dict['b']
    assert const_dict.c == normal_dict['c']
    # getitem
    for key, value in normal_dict.items():
        assert const_dict[key] == value
    # keys
    assert normal_dict.keys() == const_dict.keys()
    # setattr
    with pytest.raises(Exception):
        const_dict.a = 0
    # setitem
    with pytest.raises(Exception):
        const_dict['a'] = 0
