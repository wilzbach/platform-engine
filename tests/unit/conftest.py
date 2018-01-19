# -*- coding: utf-8 -*-
from evenflow.models import Users

from pytest import fixture


@fixture
def magic(mocker):
    """
    Shorthand for mocker.MagicMock. It's magic!
    """
    return mocker.MagicMock


@fixture
def user():
    return Users('name', 'email', '@handle')
