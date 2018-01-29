# -*- coding: utf-8 -*-
from asyncy.Config import Config
from asyncy.Containers import Containers
from asyncy.Handler import Handler
from asyncy.Lexicon import Lexicon
from asyncy.models import Results, db

from pytest import fixture


@fixture
def story(magic):
    return magic()


def test_handler_init_db(mocker, config):
    mocker.patch.object(db, 'from_url')
    Handler.init_db()
    config.get.assert_called_with('database')
    db.from_url.assert_called_with(Config.get())


def test_handler_init_mongo(mocker, config):
    mocker.patch.object(Results, '__init__', return_value=None)
    result = Handler.init_mongo()
    config.get.assert_called_with('mongo')
    Results.__init__.assert_called_with(Config.get())
    assert isinstance(result, Results)


def test_build_story(mocker, config):
    story = mocker.MagicMock()
    Handler.build_story('install_id', story)
    story.backend.assert_called_with(Config.get(), Config.get(), 'install_id')
    assert story.build_tree.call_count == 1


def test_handler_run(mocker, logger, application, story):
    mocker.patch.object(Containers, 'run')
    mocker.patch.object(Containers, 'result')
    mocker.patch.object(Containers, '__init__', return_value=None)
    mocker.patch.object(Handler, 'init_mongo')
    context = {'application': application, 'story': 'story'}
    Handler.run(logger, '1', story, context)
    story.resolve.assert_called_with(logger, '1')
    Containers.__init__.assert_called_with(story.line()['container'])
    Containers.run.assert_called_with(logger, application.get_environment(),
                                      *story.resolve())
    Handler.init_mongo.assert_called_with()
    Handler.init_mongo().save.assert_called_with(application.name, 'story',
                                                 Containers.result())


def test_handler_run_if(mocker, logger, story):
    mocker.patch.object(Lexicon, 'if_condition')
    mocker.patch.object(story, 'line', return_value={'method': 'if'})
    result = Handler.run(logger, '1', story, {})
    assert result == Lexicon.if_condition()
