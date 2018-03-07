# -*- coding: utf-8 -*-
from asyncy.Mongo import Mongo
from asyncy.processing import Handler, Lexicon

from pytest import fixture


def test_handler_init_mongo(patch):
    patch.object(Mongo, '__init__', return_value=None)
    mongo = Handler.init_mongo('mongo_url')
    Mongo.__init__.assert_called_with('mongo_url')
    assert isinstance(mongo, Mongo)


def test_handler_run(patch, logger, story):
    patch.many(story, ['line', 'start_line'])
    Handler.run(logger, '1', story)
    story.line.assert_called_with('1')
    story.start_line.assert_called_with('1')


def test_handler_run_run(patch, logger, story):
    patch.object(Lexicon, 'run')
    patch.object(story, 'line', return_value={'method': 'run'})
    Handler.run(logger, '1', story)
    Lexicon.run.assert_called_with(logger, story, story.line())


def test_handler_run_if(patch, logger, story):
    patch.object(Lexicon, 'if_condition')
    patch.object(story, 'line', return_value={'method': 'if'})
    result = Handler.run(logger, '1', story)
    Lexicon.if_condition.assert_called_with(logger, story, story.line())
    assert result == Lexicon.if_condition()


def test_handler_run_next(patch, logger, story):
    patch.object(Lexicon, 'next')
    patch.object(story, 'line', return_value={'method': 'next'})
    result = Handler.run(logger, '1', story)
    Lexicon.next.assert_called_with(logger, story, story.line())
    assert result == Lexicon.next()
