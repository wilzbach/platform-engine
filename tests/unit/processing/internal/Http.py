# -*- coding: utf-8 -*-
from asyncy.processing.Services import Services
from asyncy.processing.internal import Http
from asyncy.utils.HttpUtils import HttpUtils

from pytest import fixture, mark

from tornado.httpclient import AsyncHTTPClient


@fixture
def service_patch(patch):
    patch.object(Services, 'register_internal')


@fixture
def line():
    return {}


@mark.parametrize('method', ['post', 'get'])
@mark.asyncio
async def test_service_http_fetch(patch, story, line,
                                  service_patch, async_mock, method):
    patch.object(HttpUtils, 'fetch_with_retry', new=async_mock())
    patch.object(AsyncHTTPClient, '__init__', return_value=None)
    resolved_args = {
        'url': 'https://asyncy.com',
        'headers': {
            'Content-Type': 'application/json'
        },
        'method': method,
        'body': '{"foo":"bar"}'
    }

    client_kwargs = {
        'method': method.upper(),
        'headers': resolved_args['headers'],
        'body': '{"foo":"bar"}'
    }
    result = await Http.http_post(story, line, resolved_args)
    HttpUtils.fetch_with_retry.mock.assert_called_with(
        1, story.logger, resolved_args['url'],
        AsyncHTTPClient(), client_kwargs
    )
    assert result == await HttpUtils.fetch_with_retry()


def test_service_http_init():
    Http.init()
