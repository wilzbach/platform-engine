# -*- coding: utf-8 -*-
from unittest import mock

from asyncy.processing import Story

from asyncy.App import App

from pytest import fixture, mark


@fixture
def init(patch):
    patch.object(App, '__init__', return_value=None)


@fixture
def app(config, logger):
    return App(config, logger)


def test_app_init(patch, config, logger):
    patch.object(App, 'apply')
    App(config, logger, beta_user_id=None, sentry_dsn=None, release=None)
    App.apply.assert_called_with()


@mark.asyncio
async def test_app_bootstrap(patch, app, async_mock):
    app.stories = {
        'foo': {},
        'bar': {}
    }
    patch.object(Story, 'run', new=async_mock())
    await app.bootstrap()

    assert Story.run.mock.call_count == 2
    assert Story.run.mock.mock_calls == [
        mock.call(app, app.logger, 'foo'),
        mock.call(app, app.logger, 'bar')
    ]
