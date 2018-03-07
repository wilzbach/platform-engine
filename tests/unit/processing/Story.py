# -*- coding: utf-8 -*-
import time

from asyncy.Stories import Stories
from asyncy.processing import Handler, Story

from pytest import fixture, raises


@fixture
def models(patch, application):
    patch.object(Applications, 'get_story')
    patch.object(Applications, 'get', return_value=application)


@fixture
def handler(patch):
    patch.object(Handler, 'make_environment')


def test_story_story(patch, logger):
    patch.init(Stories)
    story = Story.story(logger, 'app_id', 'story_name')
    Stories.__init__.assert_called_with(logger, 'app_id', 'story_name')
    assert isinstance(story, Stories)


def test_story_save(patch, magic, config, logger, application, story):
    mongo = magic()
    patch.object(Handler, 'init_mongo', return_value=mongo)
    patch.object(time, 'time')
    Story.save(config, logger, application, story, {}, 1)
    logger.log.assert_called_with('story-save', story.filename, application.id)
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
    Story.run.assert_called_with(config, logger, application.id, 'next.story',
                                 app=application, parent_story=story)


def test_story_run(patch, config, logger):
    patch.object(time, 'time')
    patch.many(Story, ['execute', 'save', 'story'])
    Story.run(config, logger, 'app_id', 'story_name')
    Story.story.assert_called_with(logger, 'app_id', 'story_name')
    Story.story().get.assert_called_with()
    Story.execute.assert_called_with(config, logger, Story.story())
    Story.save.assert_called_with(config, logger, Story.story(), time.time())


def test_story_run_logger(patch, config, logger, story):
    patch.object(Stories, 'get')
    patch.many(Story, ['save', 'execute'])
    Story.run(config, logger, 'app_id', 'story_name')
    assert logger.log.call_count == 2


def test_tasks_run_force_keyword(patch, config, logger, story):
    patch.object(Stories, 'get')
    patch.many(Story, ['save', 'execute'])
    with raises(TypeError):
        Story.run(config, logger, 'app_id', 'story_name', 'story_id')


def test_story_run_with_id(patch, config, logger, story):
    patch.object(Stories, 'get')
    patch.many(Story, ['save', 'execute'])
    Story.run(config, logger, 'app_id', 'story_name', story_id='story_id')
