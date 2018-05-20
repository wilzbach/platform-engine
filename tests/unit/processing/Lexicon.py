# -*- coding: utf-8 -*-
from unittest.mock import Mock

from asyncy import Exceptions
from asyncy.Containers import Containers
from asyncy.constants.ContextConstants import ContextConstants
from asyncy.processing import Lexicon
from asyncy.processing.internal.HttpEndpoint import HttpEndpoint

import pytest
from pytest import fixture, mark


@fixture
def line():
    return {'enter': '2', 'exit': '25', 'ln': '1', 'container': 'alpine',
            'args': ['args']}


@fixture
def http_line():
    return {
        'ln': '1',
        'container': 'http-endpoint',
        'next': '2',
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'method',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'get'
                }
            },
            {
                '$OBJECT': 'argument',
                'name': 'path',
                'argument': {
                    '$OBJECT': 'string',
                    'string': '/foo'
                }
            }
        ]
    }


@fixture
def story(patch, story):
    patch.many(story, ['end_line', 'resolve', 'resolve_command', 'next_line',
                       'context', 'next_block'])
    return story


def test_lexicon_run(patch, logger, story, line):
    patch.object(Containers, 'exec')
    result = Lexicon.run(logger, story, line)
    story.resolve_command.assert_called_with(line)
    Containers.exec.assert_called_with(logger, story, line['container'],
                                       story.resolve_command())
    story.end_line.assert_called_with(line['ln'],
                                      output=Containers.exec(),
                                      assign=None)
    story.next_line.assert_called_with(line['ln'])
    assert result == story.next_line()['ln']


def test_lexicon_run_none(patch, logger, story, line):
    story.next_line.return_value = None
    patch.object(Containers, 'exec')
    result = Lexicon.run(logger, story, line)
    assert result is None


def test_lexicon_run_log(patch, logger, story, line):
    story.resolve_command.return_value = 'log'
    result = Lexicon.run(logger, story, line)
    story.resolve_command.assert_called_with(line)
    story.end_line.assert_called_with(line['ln'])
    story.next_line.assert_called_with(line['ln'])
    assert result == story.next_line()['ln']


def test_lexicon_run_log_none(patch, logger, story, line):
    story.resolve_command.return_value = 'log'
    story.next_line.return_value = None
    result = Lexicon.run(logger, story, line)
    assert result is None


def test_lexicon_set(patch, logger, story):
    story.context = {}
    line = {'ln': '1', 'args': [{'paths': ['name']}, 'values']}
    story.resolve.return_value = 'resolved'
    result = Lexicon.set(logger, story, line)
    story.resolve.assert_called_with(line['args'][1])
    story.next_line.assert_called_with('1')
    story.end_line.assert_called_with(line['ln'],
                                      assign={'paths': ['name']},
                                      output='resolved')
    assert result == story.next_line()['ln']


def test_lexicon_if(logger, story, line):
    story.context = {}
    result = Lexicon.if_condition(logger, story, line)
    logger.log.assert_called_with('lexicon-if', line, story.context)
    story.resolve.assert_called_with(line['args'][0], encode=False)
    assert result == line['enter']


def test_lexicon_if_false(logger, story, line):
    story.context = {}
    story.resolve.return_value = False
    assert Lexicon.if_condition(logger, story, line) == line['exit']


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


def test_lexicon_for_loop(patch, logger, story, line):
    patch.object(Lexicon, 'run')
    line['args'] = [
        'element',
        {'$OBJECT': 'path', 'paths': ['elements']}
    ]
    story.context = {'elements': ['one']}
    story.resolve.return_value = ['one']
    story.environment = {}
    result = Lexicon.for_loop(logger, story, line)
    Lexicon.run.assert_called_with(logger, story, line['ln'])
    assert result == line['exit']


def test_lexicon_run_http_endpoint(patch, logger, story, http_line):
    return_values = Mock()
    return_values.side_effect = ['get', '/']
    patch.object(HttpEndpoint, 'register_http_endpoint')
    story.resolve.side_effect = return_values
    story.next_line.return_value = None

    Lexicon.run(logger, story, http_line)

    HttpEndpoint.register_http_endpoint.assert_called_with(
        line=http_line['next'], method='get', path='/',
        story=story)

    story.next_block.assert_called_with(http_line)


@mark.parametrize('args', [[None, '/'], ['get', None]])
def test_lexicon_run_http_endpoint_no_method(patch, logger, story,
                                             http_line, args):
    with pytest.raises(Exceptions.ArgumentNotFoundError):
        return_values = Mock()
        return_values.side_effect = args
        story.resolve.side_effect = return_values
        story.next_line.return_value = None

        Lexicon.run(logger, story, http_line)


@mark.parametrize('http_object', ['request', 'response'])
def test_lexicon_run_http_request_response(patch, logger, story, http_object):
    http_object_line = {
        'ln': '1',
        'container': http_object
    }

    story.context.return_value = {
        ContextConstants.server_request: 'foo'
    }

    story.container = http_object
    patch.object(HttpEndpoint, 'run')

    Lexicon.run(logger, story, http_object_line)

    HttpEndpoint.run.assert_called_with(story, http_object_line)
    story.end_line.assert_called()
