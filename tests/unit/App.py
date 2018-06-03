# -*- coding: utf-8 -*-
import os

from asyncy.App import App

from pytest import fixture


@fixture
def init(patch):
    patch.object(App, '__init__', return_value=None)


@fixture
def app(config):
    return App(config)


def test_app_init(patch, config):
    patch.object(App, 'apply')
    App(config, beta_user_id=None, sentry_dsn=None, release=None)
    App.apply.assert_called_with()
