# -*- coding: utf-8 -*-
import time
from datetime import datetime

from asyncy.models import Applications
from asyncy.tasks import Handler, Story

from pytest import fixture, raises


@fixture
def models(mocker, application):
    mocker.patch.object(Applications, 'get_story')
    mocker.patch.object(Applications, 'get', return_value=application)


@fixture
def handler(patch):
    patch.object(Handler, 'init_db')
    patch.object(Handler, 'build_story')
    patch.object(Handler, 'make_environment')


def test_story_save(patch, magic, config, application, story, context):
    mongo = magic()
    patch.object(Handler, 'init_mongo', return_value=mongo)
    patch.object(time, 'time')
    Story.save(config, application, story, {}, context, 1)
    Handler.init_mongo.assert_called_with(config.mongo)
    mongo.story.assert_called_with(application.id, story.id)
    mongo.narration.assert_called_with(mongo.story(), application.initial_data,
                                       {}, story.version, 1, time.time())
    mongo.lines.assert_called_with(mongo.narration(), context['results'])


def test_story_execute(patch, logger, application, story, context):
    patch.object(Handler, 'run', return_value=0)
    Story.execute(logger, application, story, context)
    Handler.run.assert_called_with(logger, '1', story, context)


def test_story_run(patch, config, logger, application, models, handler):
    patch.object(time, 'time')
    patch.object(Story, 'save')
    patch.object(Story, 'execute')
    Story.run(config, logger, 'app_id', 'story_name')
    Handler.init_db.assert_called_with(config.database)
    Applications.get.assert_called_with(True)
    application.get_story.assert_called_with('story_name')
    story = application.get_story()
    installation_id = application.user.installation_id
    story.data.assert_called_with(application.initial_data)
    Handler.build_story.assert_called_with(config.github['app_identifier'],
                                           config.github['pem_path'],
                                           installation_id, story)
    Handler.make_environment.assert_called_with(story, application)
    context = {'application': Applications.get(), 'story': 'story_name',
               'results': {}, 'environment': Handler.make_environment()}
    Story.execute.assert_called_with(logger, application, story, context)
    Story.save.assert_called_with(config, application, story,
                                  Handler.make_environment(), context,
                                  time.time())


def test_story_run_logger(patch, config, logger, application, models, handler):
    patch.object(Story, 'save')
    patch.object(Story, 'execute')
    Story.run(config, logger, 'app_id', 'story_name')
    logger.log.assert_called_with('task-start', 'app_id', 'story_name', None)


def test_tasks_run_force_keyword(patch, config, logger, models, handler):
    patch.object(Story, 'save')
    patch.object(Story, 'execute')
    with raises(TypeError):
        Story.run(config, logger, 'app_id', 'story_name', 'story_id')


def test_story_run_with_id(patch, config, logger, models, handler):
    patch.object(Story, 'save')
    patch.object(Story, 'execute')
    Story.run(config, logger, 'app_id', 'story_name', story_id='story_id')
