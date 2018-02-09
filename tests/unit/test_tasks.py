# -*- coding: utf-8 -*-
import time
from datetime import datetime

from asyncy.Handler import Handler
from asyncy.Tasks import Tasks
from asyncy.models import Applications

from pytest import fixture, raises


@fixture
def models(mocker, application):
    mocker.patch.object(Applications, 'get_story')
    mocker.patch.object(Applications, 'get', return_value=application)


@fixture
def handler(patch):
    patch.object(Handler, 'run', return_value=0)
    patch.object(Handler, 'init_db')
    patch.object(Handler, 'init_mongo')
    patch.object(Handler, 'build_story')
    patch.object(Handler, 'make_environment')


def test_process_story(patch, config, logger, application, models, handler):
    patch.object(time, 'time')
    Tasks.process_story(config, logger, 'app_id', 'story_name')
    Handler.init_db.assert_called_with()
    Applications.get.assert_called_with(True)
    application.get_story.assert_called_with('story_name')
    story = application.get_story()
    installation_id = application.user.installation_id
    story.data.assert_called_with(application.initial_data)
    Handler.init_mongo.assert_called_with()
    Handler.init_mongo().story.assert_called_with(application.id, story.id)
    Handler.build_story.assert_called_with(installation_id, story)
    Handler.make_environment.assert_called_with(story, application)
    context = {'application': Applications.get(), 'story': 'story_name',
               'results': {}, 'environment': Handler.make_environment()}
    Handler.run.assert_called_with(logger, '1', story, context)
    Handler.init_mongo().narration.assert_called_with(Handler.init_mongo().story(),
                                                      application.initial_data,
                                                      Handler.make_environment(),
                                                      story.version,
                                                      time.time(),
                                                      time.time())
    Handler.init_mongo().lines.assert_called_with(Handler.init_mongo().narration(),
                                                {})


def test_process_story_logger(config, logger, application, models, handler):
    Tasks.process_story(config, logger, 'app_id', 'story_name')
    logger.log.assert_called_with('task-start', 'app_id', 'story_name', None)


def test_process_story_force_keyword(config, logger, models, handler):
    with raises(TypeError):
        Tasks.process_story(config, logger, 'app_id', 'story_name', 'story_id')


def test_process_story_with_id(config, logger, models, handler):
    Tasks.process_story(config, logger, 'app_id', 'story_name',
                        story_id='story_id')
