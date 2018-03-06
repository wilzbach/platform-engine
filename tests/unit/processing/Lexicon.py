# -*- coding: utf-8 -*-
from asyncy.processing import Lexicon

from pytest import fixture, mark


@fixture
def line():
    return {'enter': '2', 'exit': '25', 'ln': '1'}


def test_lexicon_if(patch, logger, story, line):
    patch.object(story, 'resolve')
    result = Lexicon.if_condition(logger, story, line)
    story.resolve.assert_called_with(logger, line['ln'])
    assert result == line['enter']


def test_lexicon_if_false(patch, logger, story, line):
    patch.object(story, 'resolve', return_value=[False])
    assert Lexicon.if_condition(logger, story, line) == line['exit']


def test_lexicon_unless(line):
    assert Lexicon.unless_condition(line, [True]) == 'exit'


def test_lexicon_unless_false(line):
    assert Lexicon.unless_condition(line, [False]) == 'enter'


@mark.parametrize('string', ['hello', 'hello.story'])
def test_lexicon_next(string):
    assert Lexicon.next(string) == 'hello.story'
