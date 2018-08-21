# -*- coding: utf-8 -*-
import json
from unittest.mock import MagicMock, Mock

from asyncy import Exceptions, Metrics
from asyncy.Exceptions import AsyncyError
from asyncy.Types import StreamingService
from asyncy.constants.ContextConstants import ContextConstants
from asyncy.constants.LineConstants import LineConstants
from asyncy.constants.ServiceConstants import ServiceConstants
from asyncy.processing import Lexicon, Story
from asyncy.processing.Mutations import Mutations
from asyncy.processing.Services import Services
from asyncy.processing.internal.HttpEndpoint import HttpEndpoint
from asyncy.utils.HttpUtils import HttpUtils

import pytest
from pytest import fixture, mark

from tornado.httpclient import AsyncHTTPClient


@fixture
def line():
    return {'enter': '2', 'exit': '25', 'ln': '1',
            LineConstants.service: 'alpine',
            'command': 'echo',
            'args': ['args'], 'next': '26'}


@fixture
def story(patch, story):
    patch.many(story, ['end_line', 'resolve',
                       'context', 'next_block', 'line'])
    return story


@mark.parametrize('name', ['foo_var', None])
@mark.asyncio
async def test_lexicon_execute(patch, logger, story, line, async_mock, name):
    line['enter'] = None

    if name is not None:
        line['name'] = [name]

    output = MagicMock()
    patch.object(Services, 'execute', new=async_mock(return_value=output))
    patch.object(Lexicon, 'next_line_or_none')
    result = await Lexicon.execute(logger, story, line)
    Services.execute.mock.assert_called_with(story, line)

    if name is not None:
        story.end_line.assert_called_with(line['ln'],
                                          output=output,
                                          assign={'paths': [name]})
    else:
        story.end_line.assert_called_with(line['ln'],
                                          output=output,
                                          assign=None)
    story.line.assert_called_with(line['next'])
    assert result == Lexicon.next_line_or_none()


@mark.asyncio
async def test_lexicon_execute_none(patch, logger, story, line, async_mock):
    line['enter'] = None
    story.line.return_value = None
    patch.object(Services, 'execute', new=async_mock())
    result = await Lexicon.execute(logger, story, line)
    assert result is None


@mark.asyncio
async def test_lexicon_set(patch, logger, story):
    story.context = {}
    patch.object(Lexicon, 'next_line_or_none')
    line = {'ln': '1', 'args': [{'paths': ['name']}, 'values'], 'next': '2'}
    story.resolve.return_value = 'resolved'
    result = await Lexicon.set(logger, story, line)
    story.resolve.assert_called_with(line['args'][1])
    story.end_line.assert_called_with(line['ln'],
                                      assign={'paths': ['name']},
                                      output='resolved')
    story.line.assert_called_with(line['next'])
    assert result == Lexicon.next_line_or_none()


@mark.asyncio
async def test_lexicon_set_mutation(patch, logger, story):
    story.context = {}
    patch.object(Lexicon, 'next_line_or_none')
    patch.object(Mutations, 'mutate')
    line = {
        'ln': '1',
        'args': [
            {
                'paths': ['name']
            },
            'values',
            {
                '$OBJECT': 'mutation'
            }
        ],
        'next': '2'
    }
    Mutations.mutate.return_value = 'mutated_result'
    result = await Lexicon.set(logger, story, line)
    story.resolve.assert_called_with(line['args'][1])
    story.end_line.assert_called_with(line['ln'],
                                      assign={'paths': ['name']},
                                      output='mutated_result')
    story.line.assert_called_with(line['next'])
    Mutations.mutate.assert_called_with(line['args'][2],
                                        story.resolve(), story, line)
    assert result == Lexicon.next_line_or_none()


@mark.asyncio
async def test_lexicon_set_invalid_operation(patch, logger, story):
    story.context = {}
    patch.object(Lexicon, 'next_line_or_none')
    line = {
        'ln': '1',
        'args': [
            {
                'paths': ['name']
            },
            'values',
            {
                '$OBJECT': 'foo'
            }
        ],
        'next': '2'
    }
    with pytest.raises(AsyncyError):
        await Lexicon.set(logger, story, line)


@mark.asyncio
async def test_lexicon_function(patch, logger, story, line):
    patch.object(story, 'next_block')
    patch.object(Lexicon, 'next_line_or_none', return_value='1')
    assert await Lexicon.function(logger, story, line) == '1'
    story.next_block.assert_called_with(line)


@mark.asyncio
async def test_lexicon_if(logger, story, line):
    story.context = {}
    result = await Lexicon.if_condition(logger, story, line)
    logger.log.assert_called_with('lexicon-if', line, story.context)
    story.resolve.assert_called_with(line['args'][0], encode=False)
    assert result == line['enter']


@mark.asyncio
async def test_lexicon_if_false(logger, story, line):
    story.context = {}
    story.resolve.return_value = False
    assert await Lexicon.if_condition(logger, story, line) == line['exit']


def test_lexicon_unless(logger, story, line):
    story.context = {}
    result = Lexicon.unless_condition(logger, story, line)
    logger.log.assert_called_with('lexicon-unless', line, story.context)
    story.resolve.assert_called_with(line['args'][0], encode=False)
    assert result == line['exit']


def test_lexicon_unless_false(logger, story, line):
    story.context = {}
    story.resolve.return_value = False
    assert Lexicon.unless_condition(logger, story, line) == line['enter']


@mark.asyncio
async def test_lexicon_for_loop(patch, logger, story, line, async_mock):
    patch.object(Lexicon, 'execute', new=async_mock())
    patch.object(Story, 'execute_block', new=async_mock())
    line['args'] = [
        {'$OBJECT': 'path', 'paths': ['elements']}
    ]
    line['output'] = ['element']
    story.context = {'elements': ['one']}
    story.resolve.return_value = ['one']
    story.environment = {}
    result = await Lexicon.for_loop(logger, story, line)
    Story.execute_block.mock.assert_called_with(logger, story, line)
    assert story.context['element'] == 'one'
    assert result == line['exit']


@mark.asyncio
async def test_lexicon_execute_http_endpoint(patch, logger, story,
                                             http_line, async_mock):
    return_values = Mock()
    return_values.side_effect = ['get', '/']
    patch.object(HttpEndpoint, 'register_http_endpoint', new=async_mock())
    story.resolve.side_effect = return_values

    await Lexicon.execute(logger, story, http_line)

    HttpEndpoint.register_http_endpoint.mock.assert_called_with(
        block=http_line['ln'], line=http_line, method='get', path='/',
        story=story)


@mark.parametrize('args', [[None, '/'], ['get', None]])
@mark.asyncio
async def test_lexicon_execute_http_endpoint_no_method(patch, logger, story,
                                                       http_line, args):
    with pytest.raises(Exceptions.ArgumentNotFoundError):
        return_values = Mock()
        return_values.side_effect = args
        story.resolve.side_effect = return_values

        await Lexicon.execute(logger, story, http_line)


@mark.asyncio
async def test_lexicon_execute_http_functions(patch, logger, story):
    http_object_line = {
        'ln': '1',
        LineConstants.service: 'client',
        LineConstants.command: 'body'
    }

    story.context = {
        ContextConstants.server_request: 'foo',
        ContextConstants.service_output: 'client'
    }

    patch.object(HttpEndpoint, 'run')

    await Lexicon.execute(logger, story, http_object_line)

    HttpEndpoint.run.assert_called_with(story, http_object_line)
    story.end_line.assert_called()


@mark.asyncio
async def test_lexicon_execute_streaming_container(patch, story, async_mock):
    line = {
        'enter': '10',
        'ln': '9',
        LineConstants.service: 'foo',
        'output': 'output',
        'next': '11'
    }

    patch.object(Services, 'start_container', new=async_mock())
    patch.object(Lexicon, 'next_line_or_none')
    patch.many(story, ['end_line', 'line'])
    Metrics.container_start_seconds_total = Mock()
    ret = await Lexicon.execute(story.logger, story, line)
    Services.start_container.mock.assert_called_with(story, line)
    story.end_line.assert_called_with(
        line['ln'], output=Services.start_container.mock.return_value,
        assign={'paths': line.get('output')})
    Metrics.container_start_seconds_total.labels().observe.assert_called_once()
    story.line.assert_called_with(line['next'])
    Lexicon.next_line_or_none.assert_called_with(story.line())
    assert ret == Lexicon.next_line_or_none()


@mark.asyncio
async def test_lexicon_when(patch, story, async_mock):
    line = {
        'ln': '10',
        LineConstants.service: 'time-client',
        LineConstants.command: 'updates',
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'foo',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'bar'
                }
            }
        ]
    }
    story.context = {
        'time-client': StreamingService('alpine', 'time-server',
                                        'asyncy--foo-1', 'foo.com')
    }

    story.app.services = {
        'alpine': {
            ServiceConstants.config: {
                'commands': {
                    'time-server': {
                        'events': {
                            'updates': {
                                'http': {
                                    'port': 2000,
                                    'subscribe': {
                                        'method': 'post',
                                        'path': '/sub'
                                    }
                                },
                                'arguments': {
                                    'foo': 'bar'
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    story.name = 'my_event_driven_story.story'
    story.app.config.engine_host = 'localhost'
    story.app.config.engine_port = 8000

    expected_url = 'http://foo.com:2000/sub'

    expected_body = {
        'endpoint': f'http://localhost:8000/story/event?'
                    f'story={story.name}&block={line["ln"]}',
        'data': {
            'foo': 'bar'
        },
        'event': 'updates'
    }

    expected_kwargs = {
        'method': 'POST',
        'body': json.dumps(expected_body),
        'headers': {'Content-Type': 'application/json; charset=utf-8'}
    }

    patch.init(AsyncHTTPClient)
    patch.object(Lexicon, 'next_line_or_none')
    patch.object(story, 'next_block')
    patch.object(story, 'argument_by_name', return_value='bar')
    http_res = Mock()
    http_res.code = 204
    patch.object(HttpUtils, 'fetch_with_retry',
                 new=async_mock(return_value=http_res))
    ret = await Lexicon.when(story.logger, story, line)
    client = AsyncHTTPClient()
    HttpUtils.fetch_with_retry.mock.assert_called_with(
        3, story.logger, expected_url, client, expected_kwargs)
    assert ret == Lexicon.next_line_or_none()
    story.next_block.assert_called_with(line)

    http_res.code = 400
    with pytest.raises(AsyncyError):
        await Lexicon.when(story.logger, story, line)


@mark.asyncio
async def test_lexicon_when_invalid(story):
    line = {'service': 'foo', 'command': 'bar'}
    with pytest.raises(AsyncyError):
        await Lexicon.when(story.logger, story, line)
