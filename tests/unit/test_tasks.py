# -*- coding: utf-8 -*-
from evenflow.Config import Config
from evenflow.Tasks import Tasks
from evenflow.models import Applications, db

from playhouse import db_url

from pytest import fixture, raises


@fixture
def database(mocker):
    mocker.patch.object(db, 'init')
    mocker.patch.object(db_url, 'parse')
    mocker.patch.object(Applications, 'get')


def test_process_story(mocker, database):
    mocker.patch.object(Config, 'get')
    result = Tasks.process_story('app_id', 'story_name')
    Config.get.assert_called_with('database')
    db_url.parse.assert_called_with(Config.get())
    db.init.assert_called_with(db_url.parse())
    Applications.get.assert_called_with(True)
    assert result


def test_process_story_force_keyword(database):
    with raises(TypeError):
        Tasks.process_story('app_id', 'story_name', 'story_id')


def test_process_story_with_id(database):
    result = Tasks.process_story('app_id', 'story_name', story_id='story_id')
    assert result
