# -*- coding: utf-8 -*-
from unittest import mock

from asyncy.App import App
from asyncy.processing import Story

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
@mark.parametrize('story_method', ['run', 'destroy'])
async def test_app_bootstrap_destroy(patch, app, async_mock,
                                     story_method):
    app.stories = {
        'foo': {},
        'bar': {}
    }
    patch.object(Story, story_method, new=async_mock())
    if story_method == 'run':
        await getattr(app, 'bootstrap')()
    elif story_method == 'destroy':
        await getattr(app, 'destroy')()

    assert getattr(Story, story_method).mock.call_count == 2
    assert getattr(Story, story_method).mock.mock_calls == [
        mock.call(app, app.logger, 'foo'),
        mock.call(app, app.logger, 'bar')
    ]
