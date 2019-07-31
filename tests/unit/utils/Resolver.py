# -*- coding: utf-8 -*-
import pytest

from storyruntime.utils import Resolver

# Note: Actual resolution tests for resolution are in integration/Lexicon.


def test_expression_invalid_type():
    with pytest.raises(Exception):
        assert Resolver.expression(
            {'expression': 'a', 'values': [b'asd']}, {}) == 1
