# -*- coding: utf-8 -*-
from storyruntime.constants.LineSentinels import LineSentinels, _Sentinel


def test_sentinel_class():
    s = _Sentinel('hello')
    assert str(s) == '_Sentinel#hello'
    assert LineSentinels.is_sentinel(s)
    assert not LineSentinels.is_not_sentinel(s)


def test_sentinels():
    assert LineSentinels.BREAK is not None
    assert LineSentinels.RETURN is not None
