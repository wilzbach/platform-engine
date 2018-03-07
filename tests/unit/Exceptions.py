# -*- coding: utf-8 -*-
from asyncy.Exceptions import AsyncyError

from pytest import raises


def test_asyncy_error():
    with raises(AsyncyError):
        raise AsyncyError('things happen')
