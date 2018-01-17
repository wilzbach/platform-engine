# -*- coding: utf-8 -*-
from evenflow.Config import Config
from evenflow.Handler import Handler
from evenflow.Tasks import Tasks
from evenflow.models import Applications, Stories

from pytest import fixture, raises


@fixture
def models(mocker):
    mocker.patch.object(Applications, 'get')
    mocker.patch.object(Stories, 'select')


@fixture
def handler_run(mocker):
    mocker.patch.object(Handler, 'run', return_value=0)


def test_process_story(mocker, models, handler_run):
    mocker.patch.object(Config, 'get')
    mocker.patch.object(Handler, 'init_db')
    mocker.patch.object(Handler, 'build_story')

    Tasks.process_story('app_id', 'story_name')

    Handler.init_db.assert_called_with()
    Applications.get.assert_called_with(True)
    Stories.select().where.assert_called_with(True)
    Stories.select().where().where.assert_called_with(True)
    Stories.select().where().where().get.assert_called_with()
    query_result = Stories.select().where().where().get()
    Handler.build_story.assert_called_with(query_result)
    context = {'application': Applications.get(), 'story': 'story_name'}
    Handler.run.assert_called_with('1', Applications.get().initial_data,
                                   context)


def test_process_story_force_keyword(models, handler_run):
    with raises(TypeError):
        Tasks.process_story('app_id', 'story_name', 'story_id')


def test_process_story_with_id(models, handler_run):
    Tasks.process_story('app_id', 'story_name', story_id='story_id')
