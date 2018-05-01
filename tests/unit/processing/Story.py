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
    patch.object(time, 'time')
    Story.save(config, logger, story, 1)
    logger.log.assert_called_with('story-save', story.name, story.app_id)


def test_story_execute(patch, config, logger, story):
    patch.object(Handler, 'run', return_value=None)
    patch.object(Stories, 'first_line')
    Story.execute(config, logger, story)
    assert Stories.first_line.call_count == 1
    logger.log.assert_called_with('story-execution', None)
    Handler.run.assert_called_with(logger, Stories.first_line(), story)


def test_story_execute_next(patch, config, logger, story):
    patch.object(Handler, 'run',
                 return_value='next.story')
    patch.object(Stories, 'first_line')
    patch.object(Story, 'run', return_value=None)
    Story.execute(config, logger, story)
    Story.run.assert_called_with(config, logger, story.app_id, 'next.story')


def test_story_run(patch, config, logger):
    patch.object(time, 'time')
    patch.many(Story, ['execute', 'save', 'story'])
    Story.run(config, logger, 'app_id', 'story_name')
    Story.story.assert_called_with(config, logger, 'app_id', 'story_name')
    Story.story().get.assert_called_with()
    Story.story().prepare.assert_called_with(None, None, None, None)
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


def test_story_run_prepare(patch, config, logger):
    patch.many(Story, ['execute', 'save', 'story'])
    kwargs = {'start': 'start', 'block': 'block', 'environment': 'env',
              'context': 'context'}
    Story.run(config, logger, 'app_id', 'story_name', **kwargs)
    Story.story().prepare.assert_called_with('env', 'context', 'start',
                                             'block')
