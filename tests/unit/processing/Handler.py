# -*- coding: utf-8 -*-
from asyncy.models import Mongo
from asyncy.processing import Handler, Lexicon

from pytest import fixture


@fixture
def story(magic):
    return magic()


def test_handler_init_mongo(patch):
    patch.object(Mongo, '__init__', return_value=None)
    mongo = Handler.init_mongo('mongo_url')
    Mongo.__init__.assert_called_with('mongo_url')
    assert isinstance(mongo, Mongo)


def test_handler_make_environment(patch, logger, story, application):
    patch.object(story, 'environment', return_value={'one': 1, 'two': 2})
    patch.object(application, 'environment', return_value={'one': 0,
                                                           'three': 3})
    environment = Handler.make_environment(logger, story, application)
    story.environment.assert_called_with()
    application.environment.assert_called_with(story.filename)
    logger.log.assert_called_with('container-environment', environment)
    assert environment == {'one': 0, 'two': 2}


def test_handler_run(patch, logger, application, story):
    patch.object(story, 'line', return_value={'method': 'run'})
    patch.object(Lexicon, 'run')
    Handler.run(logger, '1', story, 'environment')
    story.start_line.assert_called_with('1')
    Lexicon.run.assert_called_with(logger, story, story.line(), 'environment')


def test_handler_run_if(mocker, logger, story):
    mocker.patch.object(Lexicon, 'if_condition')
    mocker.patch.object(story, 'line', return_value={'method': 'if'})
    result = Handler.run(logger, '1', story, 'environment')
    Lexicon.if_condition.assert_called_with(logger, story, story.line())
    assert result == Lexicon.if_condition()


def test_handler_run_next(patch, logger, story):
    patch.object(Lexicon, 'next')
    patch.object(story, 'line', return_value={'method': 'next'})
    result = Handler.run(logger, '1', story, 'environment')
    Lexicon.next.assert_called_with(logger, story, story.line())
    assert result == Lexicon.next()
