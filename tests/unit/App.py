# -*- coding: utf-8 -*-
import json
from unittest import mock

from asyncy.App import App
from asyncy.Kubernetes import Kubernetes
from asyncy.Types import StreamingService
from asyncy.constants.ServiceConstants import ServiceConstants
from asyncy.processing import Story
from asyncy.utils.HttpUtils import HttpUtils

import pytest
from pytest import fixture, mark

from tornado.httpclient import AsyncHTTPClient


@fixture
def exc(patch):
    def func(*args):
        raise Exception()

    return func


@fixture
def app(config, logger, magic):
    return App('app_id', 'app_dns', logger, config,
               magic(), magic(), magic(), {})


def test_add_subscription(patch, app, magic):
    streaming_service = magic()
    payload = {'payload': True}
    app.add_subscription('sub_id', streaming_service, 'event_name',
                         payload)
    sub = app.get_subscription('sub_id')
    assert sub.streaming_service == streaming_service
    assert sub.id == 'sub_id'
    assert sub.payload == payload
    assert sub.event == 'event_name'
    app.remove_subscription('sub_id')
    assert app.get_subscription('sub_id') is None


@mark.asyncio
@mark.parametrize('response_code', [200, 500])
async def test_unsubscribe_all(patch, app, async_mock, magic, response_code):
    streaming_service = StreamingService('alpine', 'echo', 'alpine-1',
                                         'alpine.com')

    payload = {
        'payload': True
    }
    app.add_subscription('sub_id', streaming_service, 'event_name',
                         payload)

    app.add_subscription('sub_id_with_no_unsub',
                         streaming_service, 'foo',
                         payload)

    app.services = {
        'alpine': {
            ServiceConstants.config: {
                'actions': {
                    'echo': {
                        'events': {
                            'event_name': {
                                'http': {
                                    'unsubscribe': {
                                        'port': 28,
                                        'path': '/unsub'
                                    }
                                }
                            },
                            'foo': {
                                'http': {}
                            }
                        }
                    }
                }
            }
        }
    }

    res = magic()
    res.code = response_code
    patch.object(HttpUtils, 'fetch_with_retry',
                 new=async_mock(return_value=res))

    patch.init(AsyncHTTPClient)

    client = AsyncHTTPClient()

    await app.unsubscribe_all()

    url = 'http://alpine.com:28/unsub'
    expected_kwargs = {
        'method': 'POST',
        'body': json.dumps(payload),
        'headers': {
            'Content-Type': 'application/json; charset=utf-8'
        }
    }

    HttpUtils.fetch_with_retry.mock.assert_called_with(
        3, app.logger, url, client, expected_kwargs)

    if response_code != 200:
        app.logger.error.assert_called_once()


@mark.parametrize('env', [{'env': True}, None, {'a': {'nested': '1'}}])
def test_app_init(magic, config, logger, env):
    services = magic()
    stories = magic()
    expected_secrets = {}
    if env:
        for k, v in env.items():
            if not isinstance(v, dict):
                expected_secrets[k.lower()] = v

    app = App('app_id', 'app_dns', logger, config, logger,
              stories, services, env)
    assert app.app_id == 'app_id'
    assert app.app_dns == 'app_dns'
    assert app.config == config
    assert app.logger == logger
    assert app.stories == stories['stories']
    assert app.services == services
    assert app.environment == env
    assert app.app_context['secrets'] == expected_secrets
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
async def test_app_destroy_no_stories(patch, async_mock, app):
    app.stories = None
    patch.object(Kubernetes, 'clean_namespace', new=async_mock())
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
async def test_app_destroy(patch, app, async_mock):
    app.stories = {
        'foo': {},
        'bar': {}
    }
    app.entrypoint = ['foo', 'bar']
    patch.object(Kubernetes, 'clean_namespace', new=async_mock())
    patch.object(app, 'unsubscribe_all', new=async_mock())
    await app.destroy()

    app.unsubscribe_all.mock.assert_called()
    Kubernetes.clean_namespace.mock.assert_called()
