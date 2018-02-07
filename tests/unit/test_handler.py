# -*- coding: utf-8 -*-
from asyncy.Config import Config
from asyncy.Containers import Containers
from asyncy.Handler import Handler
from asyncy.Lexicon import Lexicon
from asyncy.models import Mongo, db

from pytest import fixture


@fixture
def story(magic):
    return magic()


def test_handler_init_db(mocker, config):
    mocker.patch.object(db, 'from_url')
    Handler.init_db()
    config.get.assert_called_with('database')
    db.from_url.assert_called_with(Config.get())


def test_handler_init_mongo(patch, config):
    patch.object(Mongo, '__init__', return_value=None)
    mongo = Handler.init_mongo()
    config.get.assert_called_with('mongo')
    Mongo.__init__.assert_called_with(Config.get())
    assert isinstance(mongo, Mongo)


def test_build_story(mocker, config):
    story = mocker.MagicMock()
    Handler.build_story('install_id', story)
    story.backend.assert_called_with(Config.get(), Config.get(), 'install_id')
    assert story.build_tree.call_count == 1


def test_handler_run(patch, logger, application, story, context):
    patch.object(Containers, 'run')
    patch.object(Containers, 'environment')
    patch.object(Containers, 'make_volume')
    patch.object(Containers, 'result')
    patch.object(Containers, '__init__', return_value=None)
    Handler.run(logger, '1', story, context)
    story.resolve.assert_called_with(logger, '1')
    Containers.__init__.assert_called_with(story.line()['container'])
    Containers.environment.assert_called_with(story, application)
    Containers.make_volume.assert_called_with(story.filename)
    Containers.run.assert_called_with(logger, story.resolve())
    assert context['results']['1'] == Containers.result()


def test_handler_run_if(mocker, logger, story):
    mocker.patch.object(Lexicon, 'if_condition')
    mocker.patch.object(story, 'line', return_value={'method': 'if'})
    result = Handler.run(logger, '1', story, {})
    assert result == Lexicon.if_condition()
