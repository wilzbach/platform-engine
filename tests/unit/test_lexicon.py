# -*- coding: utf-8 -*-
from evenflow.Lexicon import Lexicon

from pytest import fixture


@fixture
def line():
    return {'enter': 'enter', 'exit': 'exit'}


def test_lexicon_if(line):
    assert Lexicon.if_condition(line, [True]) == 'enter'


def test_lexicon_if_false(line):
    assert Lexicon.if_condition(line, [False]) == 'exit'
