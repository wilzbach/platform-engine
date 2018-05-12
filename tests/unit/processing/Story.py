# -*- coding: utf-8 -*-
import time

from asyncy.Stories import Stories
from asyncy.processing import Handler, Story

from pytest import fixture, raises


def test_story_story(patch, app, logger):
    patch.init(Stories)
    story = Story.story(app, logger, 'story_name')
    Stories.__init__.assert_called_with(app, 'story_name', logger)
    assert isinstance(story, Stories)


def test_story_execute(patch, app, logger, story):
    patch.object(Handler, 'run', return_value=None)
    patch.object(Stories, 'first_line')
    Story.execute(app, logger, story)
    assert Stories.first_line.call_count == 1
    logger.log.assert_called_with('story-execution', None)
    Handler.run.assert_called_with(logger, Stories.first_line(), story)


def test_story_execute_next(patch, app, logger, story):
    patch.object(Handler, 'run',
                 return_value='next.story')
    patch.object(Stories, 'first_line')
    patch.object(Story, 'run', return_value=None)
    Story.execute(app, logger, story)
    Story.run.assert_called_with(app, logger, 'next.story')


def test_story_run(patch, app, logger):
    patch.object(time, 'time')
    patch.many(Story, ['execute', 'story'])
    Story.run(app, logger, 'story_name')
    Story.story.assert_called_with(app, logger, 'story_name')
    Story.story().prepare.assert_called_with(None, None, None)
    Story.execute.assert_called_with(app, logger, Story.story())


def test_story_run_logger(patch, app, logger):
    patch.many(Story, ['execute', 'story'])
    Story.run(app, logger, 'story_name')
    assert logger.log.call_count == 2


def test_tasks_run_force_keyword(patch, app, logger):
    patch.many(Story, ['execute', 'story'])
    with raises(TypeError):
        Story.run(app, logger, 'story_name', 'story_id')


def test_story_run_with_id(patch, app, logger):
    patch.many(Story, ['execute', 'story'])
    Story.run(app, logger, 'story_name', story_id='story_id')


def test_story_run_prepare(patch, app, logger):
    patch.many(Story, ['execute', 'story'])
    kwargs = {'start': 'start', 'block': 'block', 'context': 'context'}
    Story.run(app, logger, 'story_name', **kwargs)
    Story.story().prepare.assert_called_with('context', 'start', 'block')
