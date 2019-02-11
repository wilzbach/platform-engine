# -*- coding: utf-8 -*-
import json
import uuid
from unittest.mock import MagicMock, Mock

from asyncy import Metrics
from asyncy.Exceptions import AsyncyError
from asyncy.Types import StreamingService
from asyncy.constants.LineConstants import LineConstants
from asyncy.constants.ServiceConstants import ServiceConstants
from asyncy.processing import Lexicon, Story
from asyncy.processing.Mutations import Mutations
from asyncy.processing.Services import Services
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
    patch.object(Lexicon, 'line_number_or_none')
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
    assert result == Lexicon.line_number_or_none()


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
    patch.object(Lexicon, 'line_number_or_none')
    line = {'ln': '1', 'name': ['out'], 'args': ['values'], 'next': '2'}
    story.resolve.return_value = 'resolved'
    result = await Lexicon.set(logger, story, line)
    story.resolve.assert_called_with(line['args'][0])
    story.end_line.assert_called_with(
        line['ln'], assign={'paths': ['out'], '$OBJECT': 'path'},
        output='resolved')
    story.line.assert_called_with(line['next'])
    assert result == Lexicon.line_number_or_none()


@mark.asyncio
async def test_lexicon_set_mutation(patch, logger, story):
    story.context = {}
    patch.object(Lexicon, 'line_number_or_none')
    patch.object(Mutations, 'mutate')
    line = {
        'ln': '1',
        'name': ['out'],
        'args': [
            'values',
            {
                '$OBJECT': 'mutation'
            }
        ],
        'next': '2'
    }
    Mutations.mutate.return_value = 'mutated_result'
    result = await Lexicon.set(logger, story, line)
    story.resolve.assert_called_with(line['args'][0])
    story.end_line.assert_called_with(
        line['ln'], assign={'paths': ['out'], '$OBJECT': 'path'},
        output='mutated_result')
    story.line.assert_called_with(line['next'])
    Mutations.mutate.assert_called_with(line['args'][1],
                                        story.resolve(), story, line)
    assert result == Lexicon.line_number_or_none()


@mark.asyncio
async def test_lexicon_set_invalid_operation(patch, logger, story):
    story.context = {}
    patch.object(Lexicon, 'line_number_or_none')
    line = {
        'ln': '1',
        'args': [
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
    patch.object(Lexicon, 'line_number_or_none', return_value='1')
    assert await Lexicon.function(logger, story, line) == '1'
    story.next_block.assert_called_with(line)


@mark.parametrize('method', ['if', 'elif', 'else'])
@mark.parametrize('args', [[True], [1, 2, 3]])
@mark.parametrize('no_more_blocks', [True, False])
@mark.asyncio
async def test_lexicon_if(patch, logger, story, async_mock,
                          method, args, no_more_blocks):
    line = {
        'method': method,
        'args': args
    }

    patch.object(Story, 'execute_block', new=async_mock())
    patch.object(story, 'resolve', return_value=True)
    side_effect = [
        {'method': 'elif', 'ln': '1'},  # This is just to test the while loop,
        {'method': 'elif', 'ln': '2'},  # and that we're jumping blocks.
        {'method': 'elif', 'ln': '3'},
        {'method': 'else', 'ln': '4'},
        {'method': 'execute', 'ln': '5'},
        {'method': 'execute', 'ln': '5'},  # Only because it's called twice.
    ]
    if no_more_blocks:
        side_effect = [None]
    patch.object(story, 'next_block', side_effect=side_effect)

    story.context = {}

    if len(args) > 2 and method != 'else':
        with pytest.raises(AsyncyError):
            await Lexicon.if_condition(logger, story, line)
        return
    else:
        result = await Lexicon.if_condition(logger, story, line)
        if method == 'else':
            story.resolve.assert_not_called()
        else:
            story.resolve.assert_called_with(line['args'][0], encode=False)
        Story.execute_block.mock.assert_called_with(logger, story, line)

        if no_more_blocks:
            assert result is None
        else:
            assert result == '5'


@mark.parametrize('method', ['if', 'elif'])
@mark.asyncio
async def test_lexicon_if_false(patch, logger, story, async_mock,
                                method):
    line = {
        'method': method,
        'args': [True],
        'next': '2'
    }

    patch.object(Story, 'execute_block', new=async_mock())
    patch.object(story, 'resolve', return_value=False)
    patch.object(story, 'next_block', side_effect=[
        {'method': 'execute', 'ln': '2'}
    ])

    story.context = {}
    result = await Lexicon.if_condition(logger, story, line)

    story.resolve.assert_called_with(line['args'][0], encode=False)

    Story.execute_block.mock.assert_not_called()

    assert '2' == result


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
async def test_lexicon_execute_streaming_container(patch, story, async_mock):
    line = {
        'enter': '10',
        'ln': '9',
        LineConstants.service: 'foo',
        'output': 'output',
        'next': '11'
    }

    patch.object(Services, 'start_container', new=async_mock())
    patch.object(Lexicon, 'line_number_or_none')
    patch.many(story, ['end_line', 'line'])
    Metrics.container_start_seconds_total = Mock()
    ret = await Lexicon.execute(story.logger, story, line)
    Services.start_container.mock.assert_called_with(story, line)
    story.end_line.assert_called_with(
        line['ln'], output=Services.start_container.mock.return_value,
        assign={'paths': line.get('output')})
    Metrics.container_start_seconds_total.labels().observe.assert_called_once()
    story.line.assert_called_with(line['next'])
    Lexicon.line_number_or_none.assert_called_with(story.line())
    assert ret == Lexicon.line_number_or_none()


@mark.parametrize('service_name', ['http', 'unknown_service'])
@mark.asyncio
async def test_lexicon_when(patch, story, async_mock, service_name):
    ss = StreamingService(name='name', command='command',
                          container_name='container_name', hostname='hostname')
    if service_name == 'unknown_service':
        ss = 'foo'

    line = {
        LineConstants.service: 'http'
    }

    story.context = {
        'http': ss
    }

    patch.object(story, 'next_block')

    patch.object(Services, 'when', new=async_mock())
    patch.object(Lexicon, 'line_number_or_none')

    if service_name == 'unknown_service':
        with pytest.raises(AsyncyError):
            await Lexicon.when(story.logger, story, line)
    else:
        ret = await Lexicon.when(story.logger, story, line)
        story.next_block.assert_called_with(line)
        Lexicon.line_number_or_none.assert_called_with(
            story.next_block.return_value)
        assert ret == Lexicon.line_number_or_none.return_value


@mark.asyncio
async def test_return_in_when(patch, logger, story):
    tree = {
        '1': {'ln': '1', 'method': 'when'},
        '2': {'ln': '2', 'method': 'execute', 'parent': '1'},
        '3': {'ln': '3', 'method': 'if', 'parent': '1'},
        '4': {'ln': '4', 'method': 'return', 'parent': '2'},
        '5': {'ln': '5', 'method': 'execute'},
    }

    def get_line(ln):
        return tree[ln]

    patch.object(story, 'line', side_effect=get_line)
    patch.object(story, 'next_block', return_value=tree['5'])
    patch.object(Lexicon, 'line_number_or_none')

    story.tree = tree

    ret = await Lexicon.ret(logger, story, tree['4'])

    story.next_block.assert_called_with(tree['1'])
    Lexicon.line_number_or_none.assert_called_with(tree['5'])

    assert ret == Lexicon.line_number_or_none()


@mark.asyncio
async def test_return_used_outside_when(patch, logger, story):
    tree = {
        '1': {'ln': '1', 'method': 'return'},
    }
    with pytest.raises(AsyncyError):
        await Lexicon.ret(logger, story, tree['1'])


@mark.asyncio
async def test_return_used_with_args(patch, logger, story):
    tree = {
        '1': {'ln': '1', 'method': 'return', 'args': [{}]},
    }
    with pytest.raises(AsyncyError):
        await Lexicon.ret(logger, story, tree['1'])


def test_next_line_or_none():
    line = {'ln': '10'}
    assert Lexicon.line_number_or_none(line) == '10'
    assert Lexicon.line_number_or_none(None) is None


@mark.asyncio
async def test_lexicon_when_invalid(story):
    line = {'service': 'foo', 'command': 'bar'}
    with pytest.raises(AsyncyError):
        await Lexicon.when(story.logger, story, line)
