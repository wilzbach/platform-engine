# -*- coding: utf-8 -*-
import json
from collections import deque
from io import StringIO


from asyncy.Containers import Containers
from asyncy.Exceptions import AsyncyError
from asyncy.constants.LineConstants import LineConstants as Line
from asyncy.processing.Services import Command, Event, Service, Services
from asyncy.utils.HttpUtils import HttpUtils

import pytest
from pytest import mark

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPResponse


@mark.asyncio
async def test_services_execute_execute_internal(story, async_mock):
    handler = async_mock(return_value='output')

    Services.register_internal('my_service', 'my_command', {}, 'any', handler)

    assert Services.is_internal('my_service') is True
    line = {
        Line.service: 'my_service',
        Line.command: 'my_command'
    }

    assert await Services.execute(story, line) == 'output'


@mark.asyncio
async def test_services_execute_execute_external(patch, story, async_mock):
    patch.object(Services, 'execute_external', new=async_mock())
    assert Services.is_internal('foo_service') is False
    line = {
        Line.service: 'foo_service',
        Line.command: 'foo_command'
    }

    assert await Services.execute(story, line) \
        == await Services.execute_external()


@mark.asyncio
async def test_services_execute_invalid_command(story):
    Services.register_internal('my_service', 'my_command', {}, 'any', None)

    line = {
        Line.service: 'my_service',
        Line.command: 'foo_command'
    }

    with pytest.raises(AsyncyError):
        await Services.execute(story, line)


@mark.asyncio
async def test_services_execute_args(story, async_mock):
    handler = async_mock(return_value='output')

    Services.register_internal('my_service', 'my_command',
                               {'arg1': {'type': 'string'}},
                               'any', handler)

    assert Services.is_internal('my_service') is True
    line = {
        Line.service: 'my_service',
        Line.command: 'my_command',
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'arg1',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'Hello world!'
                }
            }
        ]
    }

    assert await Services.execute(story, line) == 'output'
    handler.mock.assert_called_with(story=story, line=line,
                                    resolved_args={'arg1': 'Hello world!'})


def test_services_log_registry(logger):
    Services.init(logger)
    Services.register_internal('my_service', 'my_command', {}, 'any', None)
    Services.log_internal()
    logger.log_raw.assert_called_with(
        'info', 'Discovered internal service my_service - [\'my_command\']')


def test_resolve_chain(story):
    """
    The story tested here is:
    alpine echo as client
        when client foo as echo_helper
            alpine echo
                echo_helper sonar  # This isn't possible, but OK.
            echo_helper sonar

    """
    story.app.services = {
        'alpine': {}
    }

    story.tree = {
        '1': {
            Line.method: 'execute',
            Line.service: 'alpine',
            Line.command: 'echo',
            Line.enter: '2',
            Line.output: ['client']
        },
        '2': {
            Line.method: 'when',
            Line.service: 'client',
            Line.command: 'foo',
            Line.parent: '1',
            Line.output: ['echo_helper']
        },
        '3': {
            Line.method: 'execute',
            Line.service: 'alpine',
            Line.command: 'echo',
            Line.parent: '2',
            Line.enter: '4'
        },
        '4': {
            Line.method: 'execute',
            Line.service: 'echo_helper',
            Line.command: 'sonar',
            Line.parent: '3'
        },
        '5': {
            Line.method: 'execute',
            Line.service: 'echo_helper',
            Line.command: 'sonar',
            Line.parent: '2'
        }
    }

    assert Services.resolve_chain(story, story.tree['1']) \
        == deque([Service(name='alpine'), Command(name='echo')])

    assert Services.resolve_chain(story, story.tree['2']) \
        == deque([Service(name='alpine'),
                  Command(name='echo'), Event(name='foo')])

    assert Services.resolve_chain(story, story.tree['3']) \
        == deque([Service(name='alpine'), Command(name='echo')])

    assert Services.resolve_chain(story, story.tree['4']) \
        == deque([Service(name='alpine'), Command(name='echo'),
                  Event(name='foo'), Command(name='sonar')])

    assert Services.resolve_chain(story, story.tree['5']) \
        == deque([Service(name='alpine'), Command(name='echo'),
                  Event(name='foo'), Command(name='sonar')])


@mark.asyncio
async def test_services_execute_http(patch, story, async_mock):
    chain = deque([Service(name='service'), Command(name='cmd')])
    patch.object(Containers, 'get_hostname',
                 new=async_mock(return_value='container_host'))

    command_conf = {
        'http': {
            'method': 'post',
            'port': 2771,
            'path': '/invoke'
        },
        'arguments': {
            'foo': {}
        }
    }

    expected_url = 'http://container_host:2771/invoke'

    patch.object(story, 'argument_by_name', return_value='bar')

    expected_kwargs = {
        'method': 'POST',
        'body': json.dumps({'foo': 'bar'}),
        'headers': {'Content-Type': 'application/json; charset=utf-8'}
    }

    line = {
        'ln': '1'
    }

    patch.init(AsyncHTTPClient)
    client = AsyncHTTPClient()
    response = HTTPResponse(HTTPRequest(url=expected_url), 200,
                            buffer=StringIO('{"foo": "\U0001f44d"}'),
                            headers={'Content-Type': 'application/json'})

    patch.object(HttpUtils, 'fetch_with_retry',
                 new=async_mock(return_value=response))

    ret = await Services.execute_http(story, line, chain, command_conf)
    assert ret == {'foo': '\U0001f44d'}

    HttpUtils.fetch_with_retry.mock.assert_called_with(
        3, story.logger, expected_url, client, expected_kwargs)

    # Additionally, test for other scenarios.
    response = HTTPResponse(HTTPRequest(url=expected_url), 200,
                            buffer=StringIO('foo'), headers={})

    patch.object(HttpUtils, 'fetch_with_retry',
                 new=async_mock(return_value=response))

    ret = await Services.execute_http(story, line, chain, command_conf)
    assert ret == 'foo'

    response = HTTPResponse(HTTPRequest(url=expected_url), 500)

    patch.object(HttpUtils, 'fetch_with_retry',
                 new=async_mock(return_value=response))

    with pytest.raises(AsyncyError):
        await Services.execute_http(story, line, chain, command_conf)


@mark.asyncio
async def test_services_start_container(patch, story, async_mock):
    line = {'ln': '10'}
    patch.object(Containers, 'start', new=async_mock())
    ret = await Services.start_container(story, line)
    Containers.start.mock.assert_called_with(story, line)
    assert ret == Containers.start.mock.return_value
