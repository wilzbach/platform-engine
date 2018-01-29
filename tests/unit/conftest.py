# -*- coding: utf-8 -*-
from asyncy.models import Applications, Users

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


@fixture
def application(user, magic):
    app = Applications(name='app', user=user)
    app.stories = magic()
    return app
