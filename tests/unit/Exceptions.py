# -*- coding: utf-8 -*-
from asyncy.Exceptions import AsyncyError, TooManyServices, TooManyVolumes

from pytest import raises


def test_asyncy_error():
    with raises(AsyncyError):
        raise AsyncyError('things happen')


def test_many_volumes():
    with raises(TooManyVolumes):
        raise TooManyVolumes(10, 10)


def test_many_services():
    with raises(TooManyServices):
        raise TooManyServices(10, 10)
