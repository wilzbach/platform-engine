# -*- coding: utf-8 -*-
from asyncy.Containers import Containers
from asyncy.processing import Lexicon

from celery import current_app

import dateparser

from pytest import fixture, mark


@fixture
def line():
    return {'enter': '2', 'exit': '25', 'ln': '1', 'container': 'alpine',
            'args': 'args'}


@fixture
def story(patch, story):
    patch.many(story, ['end_line', 'resolve', 'resolve_command'])
    return story


def test_lexicon_run(patch, logger, story, line):
    patch.object(Containers, 'run')
    Lexicon.run(logger, story, line)
    story.resolve_command.assert_called_with(line)
    Containers.run.assert_called_with(logger, story, line['container'],
                                      story.resolve_command())
    story.end_line.assert_called_with(line['ln'], output=Containers.run())


def test_lexicon_set(patch, logger, story):
    patch.object(story, 'next_line')
    story.context = {}
    line = {'ln': '1', 'args': [{'paths': ['name']}, 'values']}
    result = Lexicon.set(logger, story, line)
    story.resolve.assert_called_with(line['args'][1])
    story.next_line.assert_called_with('1')
    story.end_line.assert_called_with(line['ln'])
    assert story.context['name'] == story.resolve()
    assert result == story.next_line()['ln']


def test_lexicon_if(logger, story, line):
    result = Lexicon.if_condition(logger, story, line)
    story.resolve.assert_called_with(line['args'])
    assert result == line['enter']


def test_lexicon_if_false(logger, story, line):
    story.resolve.return_value = [False]
    assert Lexicon.if_condition(logger, story, line) == line['exit']


def test_lexicon_unless(logger, story, line):
    result = Lexicon.unless_condition(logger, story, line)
    story.resolve.assert_called_with(line['args'])
    assert result == line['exit']


def test_lexicon_unless_false(logger, story, line):
    story.resolve.return_value = [False]
    assert Lexicon.unless_condition(logger, story, line) == line['enter']


@mark.parametrize('string', ['hello', 'hello.story'])
def test_lexicon_next(logger, story, line, string):
    story.resolve.return_value = string
    result = Lexicon.next(logger, story, line)
    story.resolve.assert_called_with(line['args'])
    assert result == 'hello.story'


def test_lexicon_wait(patch, logger, story, line):
    patch.object(story, 'next_line')
    patch.object(current_app, 'send_task')
    patch.object(dateparser, 'parse')
    story.environment = {}
    result = Lexicon.wait(logger, story, line)
    story.resolve.assert_called_with(line['args'])
    logger.log.assert_called_with('lexicon-wait', line)
    dateparser.parse.assert_called_with('in {}'.format(story.resolve()))
    task_name = 'asyncy.CeleryTasks.process_story'
    args = [story.app_id, story.name]
    kwargs = {'block': '1', 'environment': story.environment}
    current_app.send_task.assert_called_with(task_name, args=args,
                                             kwargs=kwargs,
                                             eta=dateparser.parse())
    story.next_line.assert_called_with(line['exit'])
    story.end_line.assert_called_with(line['ln'])
    assert result == story.next_line()['ln']
