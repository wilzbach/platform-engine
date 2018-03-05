# -*- coding: utf-8 -*-
from asyncy.Containers import Containers
from asyncy.Lexicon import Lexicon
from asyncy.models import Mongo
from asyncy.tasks import Handler

from pytest import fixture


@fixture
def story(magic):
    return magic()


def test_handler_init_mongo(patch):
    patch.object(Mongo, '__init__', return_value=None)
    mongo = Handler.init_mongo('mongo_url')
    Mongo.__init__.assert_called_with('mongo_url')
    assert isinstance(mongo, Mongo)


def test_handler_make_environment(patch, story, application):
    patch.object(story, 'environment', return_value={'one': 1, 'two': 2})
    patch.object(application, 'environment', return_value={'one': 0,
                                                           'three': 3})
    environment = Handler.make_environment(story, application)
    story.environment.assert_called_with()
    application.environment.assert_called_with()
    assert environment == {'one': 0, 'two': 2}


def test_handler_run(patch, logger, application, story):
    patch.object(Containers, 'run')
    patch.object(Containers, 'make_volume')
    patch.object(Containers, 'result')
    patch.object(Containers, '__init__', return_value=None)
    Handler.run(logger, '1', story, 'environment')
    story.start_line.assert_called_with('1')
    story.resolve.assert_called_with(logger, '1')
    Containers.__init__.assert_called_with(story.line()['container'], logger)
    Containers.make_volume.assert_called_with(story.filename)
    Containers.run.assert_called_with(story.resolve(), 'environment')
    story.end_line.assert_called_with('1', Containers.result())


def test_handler_run_if(mocker, logger, story):
    mocker.patch.object(Lexicon, 'if_condition')
    mocker.patch.object(story, 'line', return_value={'method': 'if'})
    result = Handler.run(logger, '1', story, 'environment')
    assert result == Lexicon.if_condition()


def test_handler_run_next(patch, logger, story):
    patch.object(Lexicon, 'next')
    patch.object(story, 'line', return_value={'method': 'next'})
    result = Handler.run(logger, '1', story, 'environment')
    Lexicon.next.assert_called_with(story.resolve())
    assert result == Lexicon.next()
