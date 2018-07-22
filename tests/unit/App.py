# -*- coding: utf-8 -*-
import os
import traceback
from unittest import mock

from asyncy.App import App
from asyncy.processing import Story

import pytest
from pytest import fixture, mark


@fixture
def exc(patch):
    patch.object(traceback, 'print_exc')

    def func(*args):
        raise Exception()

    return func


@fixture
def app(config, logger):
    return App(config, logger)


def test_app_init(patch, config, logger):
    app = App(config, logger, beta_user_id='beta_id',
              sentry_dsn=None, release=None)
    assert app.config == config
    assert app.logger == logger
    assert app.beta_user_id == 'beta_id'


@mark.asyncio
async def test_app_bootstrap(patch, app, async_mock):
    patch.object(app, 'run_stories', new=async_mock())
    stories = {'entrypoint': ['foo'], 'stories': {'foo': {}}}
    env = {'env': {}}
    services = {'services': []}
    patch.object(app, 'load_file', side_effect=[env, stories, services])
    await app.bootstrap()

    assert app.stories == stories['stories']
    assert app.entrypoint == stories['entrypoint']
    assert app.services == services
    assert app.environment == env

    assert app.run_stories.mock.call_count == 1


def test_app_load_file(patch, app):
    import asyncy
    patch.many(asyncy.App, ['open', 'load'])
    patch.object(os.path, 'exists', return_value=True)
    path = '/config/stories.json'
    result = app.load_file(path)
    asyncy.App.open.assert_called_with(path, 'r')
    assert asyncy.App.load() == result


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

    patch.object(Story, 'run', new=async_mock(side_effect=exc))

    with pytest.raises(Exception):
        await app.run_stories()

    traceback.print_exc.assert_called_once()


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

    traceback.print_exc.assert_called_once()


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
