# -*- coding: utf-8 -*-
import time

import pytest
from pytest import mark

from storyruntime import Metrics
from storyruntime.Exceptions import StoryscriptError
from storyruntime.Story import Story
from storyruntime.processing import Lexicon, Stories


def test_stories_story(patch, app, logger):
    patch.init(Story)
    story = Stories.story(app, logger, 'story_name')
    Story.__init__.assert_called_with(app, 'story_name', logger)
    assert isinstance(story, Story)


@mark.asyncio
async def test_stories_execute(patch, app, logger, story, async_mock):
    patch.object(Lexicon, 'execute_line', new=async_mock(return_value=None))
    patch.object(Story, 'first_line')
    story.prepare()
    await Stories.execute(logger, story)
    assert Story.first_line.call_count == 1
    logger.log.assert_called_with('story-execution', None)
    Lexicon.execute_line.mock.assert_called_with(logger,
                                                 story, Story.first_line())


@mark.asyncio
async def test_stories_run(patch, app, logger, async_mock, magic):
    patch.object(time, 'time')
    patch.object(Stories, 'execute', new=async_mock())
    patch.object(Stories, 'story')
    assert Metrics.story_run_total is not None
    assert Metrics.story_run_success is not None
    Metrics.story_run_total = magic()
    Metrics.story_run_success = magic()

    await Stories.run(app, logger, 'story_name')
    Stories.story.assert_called_with(app, logger, 'story_name')
    Stories.story.return_value.prepare.assert_called_with(None)
    Stories.execute.mock.assert_called_with(logger, Stories.story())

    Metrics.story_run_total.labels.assert_called_with(app_id=app.app_id,
                                                      story_name='story_name')
    Metrics.story_run_total.labels.return_value.observe.assert_called_once()

    Metrics.story_run_success.labels \
        .assert_called_with(app_id=app.app_id, story_name='story_name')
    Metrics.story_run_success.labels.return_value.observe.assert_called_once()


@mark.asyncio
async def test_stories_run_metrics_exc(patch, app, logger, async_mock, magic):
    patch.object(time, 'time')
    assert Metrics.story_run_total is not None
    assert Metrics.story_run_failure is not None
    Metrics.story_run_total = magic()
    Metrics.story_run_failure = magic()

    def exc(*args, **kwargs):
        raise Exception()

    patch.object(Stories, 'execute', new=async_mock(side_effect=exc))
    patch.object(Stories, 'story')
    with pytest.raises(Exception):
        await Stories.run(app, logger, 'story_name')
    Stories.story.assert_called_with(app, logger, 'story_name')
    Stories.story.return_value.prepare.assert_called_with(None)
    Stories.execute.mock.assert_called_with(logger, Stories.story())

    Metrics.story_run_total.labels.assert_called_with(app_id=app.app_id,
                                                      story_name='story_name')
    Metrics.story_run_total.labels.return_value.observe.assert_called_once()

    Metrics.story_run_failure.labels \
        .assert_called_with(app_id=app.app_id, story_name='story_name')
    Metrics.story_run_failure.labels.return_value.observe.assert_called_once()


@mark.asyncio
async def test_stories_run_logger(patch, app, logger, async_mock):
    patch.object(Stories, 'execute', new=async_mock())
    patch.object(Stories, 'story')
    await Stories.run(app, logger, 'story_name')
    assert logger.log.call_count == 2


def test_stories_save_logger(logger, story):
    story.app_id = 'app_id'
    Stories.save(logger, story, None)
    assert logger.log.call_count == 1


@mark.asyncio
async def test_stories_run_with_id(patch, app, logger, async_mock):
    patch.object(Stories, 'execute', new=async_mock())
    patch.object(Stories, 'story')
    await Stories.run(app, logger, 'story_name', story_id='story_id')


@mark.asyncio
async def test_stories_run_prepare_function(patch, app, logger, async_mock):
    patch.object(Stories, 'story')
    function_name = 'function_name'
    with pytest.raises(StoryscriptError):
        await Stories.run(app, logger, 'story_name',
                          context='context', function_name=function_name)


@mark.asyncio
async def test_stories_run_prepare_block(patch, app, logger, async_mock):
    patch.object(Lexicon, 'execute_block', new=async_mock())
    patch.object(Stories, 'story')
    block = '1'
    await Stories.run(app, logger, 'story_name',
                      context='context', block=block)
    Stories.story().prepare.assert_called_with('context')
    Stories.story().line.assert_called_with(block)
    Stories.story().new_frame.assert_called_with(block)
    Lexicon.execute_block.mock \
        .assert_called_with(logger, Stories.story(),
                            Stories.story().line())


@mark.asyncio
async def test_stories_run_prepare(patch, app, logger, async_mock):
    patch.object(Stories, 'execute', new=async_mock())
    patch.object(Stories, 'story')
    await Stories.run(app, logger, 'story_name',
                      context='context')
    Stories.story().prepare.assert_called_with('context')
    Stories.execute.mock \
        .assert_called_with(logger, Stories.story())
