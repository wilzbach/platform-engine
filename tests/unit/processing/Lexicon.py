# -*- coding: utf-8 -*-
from asyncy.processing import Lexicon

from pytest import fixture, mark


@fixture
def line():
    return {'enter': '2', 'exit': '25', 'ln': '1'}


@fixture
def story(patch, story):
    patch.object(story, 'resolve')
    return story


def test_lexicon_if(patch, logger, story, line):
    result = Lexicon.if_condition(logger, story, line)
    story.resolve.assert_called_with(logger, line['ln'])
    assert result == line['enter']


def test_lexicon_if_false(patch, logger, story, line):
    story.resolve.return_value = [False]
    assert Lexicon.if_condition(logger, story, line) == line['exit']


def test_lexicon_unless(patch, logger, story, line):
    result = Lexicon.unless_condition(logger, story, line)
    story.resolve.assert_called_with(logger, line['ln'])
    assert result == line['exit']


def test_lexicon_unless_false(patch, logger, story, line):
    story.resolve.return_value = [False]
    assert Lexicon.unless_condition(logger, story, line) == line['enter']


@mark.parametrize('string', ['hello', 'hello.story'])
def test_lexicon_next(logger, story, line, string):
    story.resolve.return_value = string
    result = Lexicon.next(logger, story, line)
    story.resolve.assert_called_with(logger, line['ln'])
    assert result == 'hello.story'
