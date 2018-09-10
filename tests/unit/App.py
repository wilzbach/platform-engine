# -*- coding: utf-8 -*-
from unittest import mock

from asyncy.App import App
from asyncy.processing import Story

import pytest
from pytest import fixture, mark


@fixture
def exc(patch):
    def func(*args):
        raise Exception()

    return func


@fixture
def app(config, logger, magic):
    return App('app_id', logger, config, magic(), magic(), magic(), magic(),
               sentry_client=magic())


def test_app_init(magic, config, logger):
    services = magic()
    environment = magic()
    stories = magic()
    sentry = magic()
    app = App('app_id', logger, config, logger, stories, services, environment,
              sentry_client=sentry)
    assert app.app_id == 'app_id'
    assert app.config == config
    assert app.logger == logger
    assert app.stories == stories['stories']
    assert app.services == services
    assert app.environment == environment
    assert app.sentry_client == sentry
    assert app.entrypoint == stories['entrypoint']


@mark.asyncio
async def test_app_bootstrap(patch, app, async_mock):
    patch.object(app, 'run_stories', new=async_mock())
    stories = {'entrypoint': ['foo'], 'stories': {'foo': {}}}
    app.stories = stories
    await app.bootstrap()

    assert app.run_stories.mock.call_count == 1


@mark.asyncio
async def test_app_run_stories(patch, app, async_mock):
    stories = {
        'foo': {},
        'bar': {}
    }
    app.entrypoint = ['foo', 'bar']
    app.stories = stories
    patch.object(Story, 'run', new=async_mock())
    await app.run_stories()
    assert Story.run.mock.call_count == 2


@mark.asyncio
async def test_app_destroy_no_stories(app):
    app.stories = None
    assert await app.destroy() is None


@mark.asyncio
async def test_app_run_stories_exc(patch, app, async_mock, exc):
    app.stories = {
        'foo': {},
        'bar': {}
    }
    app.entrypoint = ['foo', 'bar']
    patch.object(app, 'logger')

    patch.object(Story, 'run', new=async_mock(side_effect=exc))

    with pytest.raises(Exception):
        await app.run_stories()

    app.logger.error.assert_called_once()


@mark.asyncio
async def test_app_destroy_exc(patch, app, async_mock, exc):
    app.stories = {
        'foo': {},
        'bar': {}
    }
    app.entrypoint = ['foo', 'bar']

    patch.object(Story, 'destroy', new=async_mock(side_effect=exc))

    with pytest.raises(Exception):
        await app.destroy()

    app.logger.error.assert_called_once()


@mark.asyncio
async def test_app_destroy(patch, app, async_mock):
    app.stories = {
        'foo': {},
        'bar': {}
    }
    app.entrypoint = ['foo', 'bar']
    patch.object(Story, 'destroy', new=async_mock())
    await app.destroy()

    assert Story.destroy.mock.call_count == 2
    assert Story.destroy.mock.mock_calls == [
        mock.call(app, app.logger, 'foo'),
        mock.call(app, app.logger, 'bar')
    ]
