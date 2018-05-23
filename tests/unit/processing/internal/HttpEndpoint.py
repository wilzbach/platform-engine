# -*- coding: utf-8 -*-

from unittest.mock import Mock

from asyncy.constants import ContextConstants
from asyncy.processing.internal.HttpEndpoint import HttpEndpoint

import pytest
from pytest import mark

from tornado import httpclient
from tornado.httpclient import HTTPRequest


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


def test_http_endpoint_register(patch, story):
    patch.object(httpclient, 'HTTPClient')
    patch.object(HTTPRequest, '__init__', return_value=None)
    HttpEndpoint.register_http_endpoint(story, 'foo_method', 'foo_path', '28')
    url = 'http://{}/register/story'
    url = url.format(story.app.config.gateway_url)
    HTTPRequest.__init__.assert_called_with(
        url=url, method='POST',
        headers={
            'Content-Type': 'application/json; charset=utf-8'
        },
        body='{"method":"foo_method","endpoint":"foo_path",'
             '"story_name":"' + story.name + '","line":"28"}')

    httpclient.HTTPClient.return_value.fetch.assert_called_once()
    httpclient.HTTPClient.return_value.close.assert_called_once()


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
