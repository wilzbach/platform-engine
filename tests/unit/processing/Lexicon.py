# -*- coding: utf-8 -*-
import pytest

from asyncy.Containers import Containers
from asyncy.processing import Lexicon

import dateparser

from pytest import fixture, mark


@fixture
def line():
    return {'enter': '2', 'exit': '25', 'ln': '1', 'container': 'alpine',
            'args': ['args']}


@fixture
def story(patch, story):
    patch.many(story, ['end_line', 'resolve', 'resolve_command', 'next_line'])
    return story


def test_lexicon_run(patch, logger, story, line):
    patch.object(Containers, 'run')
    result = Lexicon.run(logger, story, line)
    story.resolve_command.assert_called_with(line)
    Containers.run.assert_called_with(logger, story, line['container'],
                                      story.resolve_command())
    story.end_line.assert_called_with(line['ln'],
                                      output=Containers.run(),
                                      assign=None)
    story.next_line.assert_called_with(line['ln'])
    assert result == story.next_line()['ln']


def test_lexicon_run_none(patch, logger, story, line):
    story.next_line.return_value = None
    patch.object(Containers, 'run')
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


@mark.parametrize('string', ['hello', 'hello.story'])
def test_lexicon_next(logger, story, line, string):
    story.resolve.return_value = string
    result = Lexicon.next(logger, story, line)
    story.resolve.assert_called_with(line['args'][0])
    assert result == 'hello.story'


def test_lexicon_wait(patch, logger, story, line):
    with pytest.raises(NotImplementedError):
        Lexicon.wait(logger, story, line)
    # patch.object(current_app, 'send_task')
    # patch.object(dateparser, 'parse')
    # story.environment = {}
    # result = Lexicon.wait(logger, story, line)
    # story.resolve.assert_called_with(line['args'][0])
    # logger.log.assert_called_with('lexicon-wait', line)
    # dateparser.parse.assert_called_with('in {}'.format(story.resolve()))
    # task_name = 'asyncy.CeleryTasks.process_story'
    # args = [story.app_id, story.name]
    # kwargs = {'block': '1', 'environment': story.environment}
    # current_app.send_task.assert_called_with(task_name, args=args,
    #                                          kwargs=kwargs,
    #                                          eta=dateparser.parse())
    # story.next_line.assert_called_with(line['exit'])
    # story.end_line.assert_called_with(line['ln'])
    # assert result == story.next_line()['ln']
