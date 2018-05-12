# -*- coding: utf-8 -*-
import os

from asyncy.App import App

from pytest import fixture


@fixture
def init(patch):
    patch.object(App, '__init__', return_value=None)


@fixture
def config():
    return App()


def test_app_init(patch):
    patch.object(App, 'apply')
    App()
    App.apply.assert_called_with()
