# -*- coding: utf-8 -*-
from evenflow.Config import Config
from evenflow.Handler import Handler
from evenflow.Tasks import Tasks
from evenflow.models import Applications

from pytest import fixture, raises


@fixture
def models(mocker):
    mocker.patch.object(Applications, 'get')


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
    Applications.get().stories.where.assert_called_with(True)
    Applications.get().stories.where().get.assert_called_with()
    query_result = Applications.get().stories.where().get()
    Handler.build_story.assert_called_with(query_result)
    context = {'application': Applications.get(), 'story': 'story_name'}
    Handler.run.assert_called_with('1', query_result.tree['script']['1'],
                                   Applications.get().initial_data,
                                   context)


def test_process_story_force_keyword(models, handler_run):
    with raises(TypeError):
        Tasks.process_story('app_id', 'story_name', 'story_id')


def test_process_story_with_id(models, handler_run):
    Tasks.process_story('app_id', 'story_name', story_id='story_id')
