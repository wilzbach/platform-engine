# -*- coding: utf-8 -*-
from asyncy.Containers import Containers
from asyncy.processing import Lexicon

from pytest import fixture, mark


@fixture
def line():
    return {'enter': '2', 'exit': '25', 'ln': '1', 'container': 'alpine'}


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
    story.resolve.assert_called_with(logger, line['ln'])
    Containers.__init__.assert_called_with(line['container'], logger)
    Containers.make_volume.assert_called_with(story.name)
    Containers.run.assert_called_with(story.resolve(), story.environment)
    story.end_line.assert_called_with(line['ln'], Containers.result())


def test_lexicon_if(logger, story, line):
    result = Lexicon.if_condition(logger, story, line)
    story.resolve.assert_called_with(logger, line['ln'])
    assert result == line['enter']


def test_lexicon_if_false(logger, story, line):
    story.resolve.return_value = [False]
    assert Lexicon.if_condition(logger, story, line) == line['exit']


def test_lexicon_unless(logger, story, line):
    result = Lexicon.unless_condition(logger, story, line)
    story.resolve.assert_called_with(logger, line['ln'])
    assert result == line['exit']


def test_lexicon_unless_false(logger, story, line):
    story.resolve.return_value = [False]
    assert Lexicon.unless_condition(logger, story, line) == line['enter']


@mark.parametrize('string', ['hello', 'hello.story'])
def test_lexicon_next(logger, story, line, string):
    story.resolve.return_value = string
    result = Lexicon.next(logger, story, line)
    story.resolve.assert_called_with(logger, line['ln'])
    assert result == 'hello.story'
