# -*- coding: utf-8 -*-
from evenflow.Config import Config
from evenflow.Handler import Handler
from evenflow.Tasks import Tasks
from evenflow.models import Applications, Stories

from pytest import fixture, raises


@fixture
def database(mocker):
    mocker.patch.object(Applications, 'get')
    mocker.patch.object(Stories, 'select')


def test_process_story(mocker, database):
    mocker.patch.object(Config, 'get')
    mocker.patch.object(Handler, 'init_db')
    mocker.patch.object(Handler, 'build_story')

    result = Tasks.process_story('app_id', 'story_name')

    Handler.init_db.assert_called_with()
    Applications.get.assert_called_with(True)
    Stories.select().where.assert_called_with(True)
    Stories.select().where().where.assert_called_with(True)
    Handler.build_story.assert_called_with(Stories.select().where().where())
    assert result


def test_process_story_force_keyword(database):
    with raises(TypeError):
        Tasks.process_story('app_id', 'story_name', 'story_id')


def test_process_story_with_id(database):
    result = Tasks.process_story('app_id', 'story_name', story_id='story_id')
    assert result
