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
    patch.object(story, 'resolve')
    return story


def test_lexicon_run(patch, logger, story, line):
    patch.object(story, 'end_line')
    patch.init(Containers)
    patch.many(Containers, ['run', 'result', 'make_volume'])
    story.environment = 'environment'
    Lexicon.run(logger, story, line)
    story.resolve.assert_called_with(line['args'])
    Containers.__init__.assert_called_with(line['container'], logger)
    Containers.make_volume.assert_called_with(story.name)
    Containers.run.assert_called_with(story.resolve(), story.environment)
    story.end_line.assert_called_with(line['ln'], Containers.result())


def test_lexicon_set(patch, logger, story):
    patch.object(story, 'next_line')
    story.environment = {}
    line = {'ln': '1', 'args': [{'paths': ['name']}, 'values']}
    result = Lexicon.set(logger, story, line)
    story.resolve.assert_called_with(line['args'][1])
    story.next_line.assert_called_with('1')
    assert story.environment['name'] == story.resolve()
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
    result = Lexicon.wait(logger, story, line)
    story.resolve.assert_called_with(line['args'])
    logger.log.assert_called_with('lexicon-wait', line)
    dateparser.parse.assert_called_with('in {}'.format(story.resolve()))
    task_name = 'asyncy.CeleryTasks.process_story'
    current_app.send_task.assert_called_with(task_name,
                                             args=[story.name, story.app_id],
                                             eta=dateparser.parse())
    story.next_line.assert_called_with(line['exit'])
    assert result == story.next_line()['ln']
