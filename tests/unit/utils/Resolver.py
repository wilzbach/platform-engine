# -*- coding: utf-8 -*-
from asyncy.utils import Resolver

import pytest


def test_expression_invalid_type():
    with pytest.raises(Exception):
        assert Resolver.expression(
            {'expression': 'a', 'values': [b'asd']}, {}) == 1
