# -*- coding: utf-8 -*-
import time

from asyncy.Handler import Handler
from asyncy.Tasks import Tasks
from asyncy.models import Applications

from pytest import fixture, raises


@fixture
def models(mocker, application):
    mocker.patch.object(Applications, 'get_story')
    mocker.patch.object(Applications, 'get', return_value=application)


@fixture
def handler(mocker):
    mocker.patch.object(Handler, 'run', return_value=0)
    mocker.patch.object(Handler, 'init_db')
    mocker.patch.object(Handler, 'build_story')


def test_process_story(patch, logger, application, models, handler):
    patch.object(time, 'time')
    Tasks.process_story(logger, 'app_id', 'story_name')
    Handler.init_db.assert_called_with()
    Applications.get.assert_called_with(True)
    application.get_story.assert_called_with('story_name')
    story = application.get_story()
    installation_id = application.user.installation_id
    story.data.assert_called_with(application.initial_data)
    Handler.build_story.assert_called_with(installation_id, story)
    context = {'application': Applications.get(), 'story': 'story_name',
               'start': time.time()}
    Handler.run.assert_called_with(logger, '1', story, context)


def test_process_story_logger(logger, application, models, handler):
    Tasks.process_story(logger, 'app_id', 'story_name')
    logger.log.assert_called_with('task-start', 'app_id', 'story_name', None)


def test_process_story_force_keyword(logger, models, handler):
    with raises(TypeError):
        Tasks.process_story(logger, 'app_id', 'story_name', 'story_id')


def test_process_story_with_id(logger, models, handler):
    Tasks.process_story(logger, 'app_id', 'story_name', story_id='story_id')
