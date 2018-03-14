# -*- coding: utf-8 -*-
import time

from asyncy.Stories import Stories
from asyncy.processing import Handler, Story

from pytest import fixture, raises


def test_story_story(patch, config, logger):
    patch.init(Stories)
    story = Story.story(config, logger, 'app_id', 'story_name')
    Stories.__init__.assert_called_with(config, logger, 'app_id', 'story_name')
    assert isinstance(story, Stories)


def test_story_save(patch, magic, config, logger, story):
    story.version = 'version'
    mongo = magic()
    patch.object(Handler, 'init_mongo', return_value=mongo)
    patch.object(time, 'time')
    Story.save(config, logger, story, 1)
    logger.log.assert_called_with('story-save', story.name, story.app_id)
    Handler.init_mongo.assert_called_with(config.mongo)
    mongo.story.assert_called_with(story.name, story.app_id)
    mongo.narration.assert_called_with(mongo.story(), story, story.version, 1,
                                       time.time())
    mongo.lines.assert_called_with(mongo.narration(), story.results)


def test_story_execute(patch, config, logger, story):
    patch.object(Handler, 'run', return_value=None)
    Story.execute(config, logger, story)
    logger.log.assert_called_with('story-execution', None)
    Handler.run.assert_called_with(logger, '1', story)


def test_story_execute_next(patch, config, logger, story):
    patch.object(Handler, 'run', return_value='next.story')
    patch.object(Story, 'run', return_value=None)
    Story.execute(config, logger, story)
    Story.run.assert_called_with(config, logger, story.app_id, 'next.story')


def test_story_run(patch, config, logger):
    patch.object(time, 'time')
    patch.many(Story, ['execute', 'save', 'story'])
    Story.run(config, logger, 'app_id', 'story_name')
    Story.story.assert_called_with(config, logger, 'app_id', 'story_name')
    Story.story().get.assert_called_with()
    Story.execute.assert_called_with(config, logger, Story.story())
    Story.save.assert_called_with(config, logger, Story.story(), time.time())


def test_story_run_logger(patch, config, logger):
    patch.many(Story, ['execute', 'save', 'story'])
    Story.run(config, logger, 'app_id', 'story_name')
    assert logger.log.call_count == 2


def test_tasks_run_force_keyword(patch, config, logger):
    patch.many(Story, ['execute', 'save', 'story'])
    with raises(TypeError):
        Story.run(config, logger, 'app_id', 'story_name', 'story_id')


def test_story_run_with_id(patch, config, logger):
    patch.many(Story, ['execute', 'save', 'story'])
    Story.run(config, logger, 'app_id', 'story_name', story_id='story_id')


def test_story_run_block(patch, config, logger):
    patch.many(Story, ['execute', 'save', 'story'])
    Story.run(config, logger, 'app_id', 'story_name', block='parent_line')
    Story.story().child_block.assert_called_with('parent_line')


def test_story_run_environment(patch, config, logger):
    patch.many(Story, ['execute', 'save', 'story'])
    Story.run(config, logger, 'app_id', 'story_name', environment='env')
    assert Story.story().environment == 'env'
