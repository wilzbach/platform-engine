# -*- coding: utf-8 -*-
import time

from asyncy.models import Applications, db
from asyncy.tasks import Handler, Story

from pytest import fixture, raises


@fixture
def models(mocker, application):
    mocker.patch.object(Applications, 'get_story')
    mocker.patch.object(Applications, 'get', return_value=application)


@fixture
def handler(patch):
    patch.object(Handler, 'make_environment')


def test_story_save(patch, magic, config, application, story):
    mongo = magic()
    patch.object(Handler, 'init_mongo', return_value=mongo)
    patch.object(time, 'time')
    Story.save(config, application, story, {}, 1)
    Handler.init_mongo.assert_called_with(config.mongo)
    mongo.story.assert_called_with(application.id, story.id)
    mongo.narration.assert_called_with(mongo.story(), application.initial_data,
                                       {}, story.version, 1, time.time())
    mongo.lines.assert_called_with(mongo.narration(), story.results)


def test_story_execute(patch, config, logger, application, story):
    patch.object(Handler, 'run', return_value=None)
    Story.execute(config, logger, application, story, 'environment')
    Handler.run.assert_called_with(logger, '1', story, 'environment')


def test_story_execute_next(patch, config, logger, application, story):
    patch.object(Handler, 'run', return_value='next.story')
    patch.object(Story, 'run', return_value=None)
    Story.execute(config, logger, application, story, 'environment')
    Story.run.assert_called_with(config, logger, application.id, 'next.story')


def test_story_run(patch, config, logger, application, models, handler):
    patch.object(time, 'time')
    patch.object(Story, 'save')
    patch.object(Story, 'execute')
    patch.object(db, 'from_url')
    Story.run(config, logger, 'app_id', 'story_name')
    db.from_url.assert_called_with(config.database)
    Applications.get.assert_called_with(True)
    application.get_story.assert_called_with('story_name')
    story = application.get_story()
    story.build.assert_called_with(application,
                                   config.github['app_identifier'],
                                   config.github['pem_path'])
    Handler.make_environment.assert_called_with(story, application)
    Story.execute.assert_called_with(config, logger, application, story,
                                     Handler.make_environment())
    Story.save.assert_called_with(config, application, story,
                                  Handler.make_environment(), time.time())


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


def test_story_run_with_app(patch, config, logger, application, handler):
    patch.object(Story, 'save')
    patch.object(Story, 'execute')
    Story.run(config, logger, 'app_id', 'story_name', app=application)
