# -*- coding: utf-8 -*-

from unittest.mock import Mock

from asyncy.Exceptions import AsyncyError
from asyncy.constants import ContextConstants
from asyncy.processing.internal.HttpEndpoint import HttpEndpoint
from asyncy.utils.HttpUtils import HttpUtils

import pytest
from pytest import mark

from tornado.httpclient import AsyncHTTPClient, HTTPError


@mark.parametrize('http_object', ['request', 'response', 'foo'])
def test_http_endpoint_run(patch, story, http_object):
    line = {
        'container': http_object
    }
    patch.many(HttpEndpoint, ['access_request', 'access_response'])
    if http_object is 'request':
        HttpEndpoint.run(story, line)
        HttpEndpoint.access_request.assert_called_with(story, line)
    elif http_object is 'response':
        HttpEndpoint.run(story, line)
        HttpEndpoint.access_response.assert_called_with(story, line)
    else:
        with pytest.raises(NotImplementedError):
            HttpEndpoint.run(story, line)


@mark.asyncio
async def test_http_endpoint_register(patch, story, async_mock):
    line = {}
    patch.object(HttpEndpoint, '_update_gateway', new=async_mock())
    await HttpEndpoint.register_http_endpoint(story, line, 'post', '/', '28')
    HttpEndpoint._update_gateway.mock.assert_called_with(
        story, line, 'post', 'register', '/', '28'
    )


@mark.asyncio
async def test_http_endpoint_unregister(patch, story, async_mock):
    line = {}
    patch.object(HttpEndpoint, '_update_gateway', new=async_mock())
    await HttpEndpoint.unregister_http_endpoint(story, line, 'post', '/', '28')
    HttpEndpoint._update_gateway.mock.assert_called_with(
        story, line, 'post', 'unregister', '/', '28'
    )


@mark.asyncio
@mark.parametrize('action', ['register', 'unregister'])
async def test_http_endpoint_update_gateway(patch, story, async_mock, action):
    patch.object(HttpUtils, 'fetch_with_retry', new=async_mock())
    patch.object(AsyncHTTPClient, '__init__', return_value=None)
    story.app.config.gateway_url = 'localhost:8889'
    await HttpEndpoint._update_gateway(story, {}, 'foo_method',
                                       action, 'foo_path', '28')
    url = f'http://{story.app.config.gateway_url}/{action}'
    client = AsyncHTTPClient()

    expected_kwargs = {
        'method': 'POST',
        'headers': {
            'Content-Type': 'application/json; charset=utf-8'
        },
        'body': '{"method":"foo_method","endpoint":"foo_path",'
                '"filename":"hello.story","block":"28"}'
    }

    HttpUtils.fetch_with_retry.mock \
        .assert_called_with(3, story.logger, url, client, expected_kwargs)


@mark.asyncio
async def test_http_endpoint_update_gw_with_error(patch, story, async_mock):
    def throw_error(a, b, c, d, e):
        raise HTTPError(500)

    patch.object(HttpUtils, 'fetch_with_retry',
                 new=async_mock(side_effect=throw_error))

    with pytest.raises(AsyncyError):
        await HttpEndpoint._update_gateway(
            story, {}, 'foo_method', 'register', 'foo_path', '28'
        )


@mark.parametrize('command', ['set_status', 'set_header', 'write', 'finish'])
def test_http_endpoint_access_response(patch, story, command):
    line = {
        'args': [{'paths': [command]}]
    }

    patch.object(story, 'argument_by_name')
    tornado_req = Mock()
    io_loop = Mock()

    patch.object(io_loop, 'add_callback', side_effect=lambda x: x())
    story.context = {
        ContextConstants.server_request: tornado_req,
        ContextConstants.server_io_loop: io_loop
    }

    story.argument_by_name.return_value = 'argument_val'
    HttpEndpoint.access_response(story, line)

    if command == 'set_status':
        tornado_req.write.assert_called_with(
            '{"command":"set_status","code":"argument_val"}\n')
    elif command == 'set_header':
        tornado_req.write.assert_called_with(
            '{"command":"set_header","key":"argument_val",'
            '"value":"argument_val"}\n')
    elif command == 'write':
        tornado_req.write.assert_called_with(
            '{"command":"write","content":"argument_val"}\n')
    elif command == 'finish':
        tornado_req.write.assert_called_with(
            '{"command":"finish"}\n')
        tornado_req.finish.assert_called_once()
