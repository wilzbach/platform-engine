# -*- coding: utf-8 -*-
from asyncy.processing import Lexicon

from pytest import fixture, mark


@fixture
def line():
    return {'enter': 'enter', 'exit': 'exit'}


def test_lexicon_if(line):
    assert Lexicon.if_condition(line, [True]) == 'enter'


def test_lexicon_if_false(line):
    assert Lexicon.if_condition(line, [False]) == 'exit'


def test_lexicon_unless(line):
    assert Lexicon.unless_condition(line, [True]) == 'exit'


def test_lexicon_unless_false(line):
    assert Lexicon.unless_condition(line, [False]) == 'enter'


@mark.parametrize('string', ['hello', 'hello.story'])
def test_lexicon_next(string):
    assert Lexicon.next(string) == 'hello.story'
