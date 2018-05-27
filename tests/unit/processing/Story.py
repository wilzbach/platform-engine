# -*- coding: utf-8 -*-
import time
from unittest.mock import Mock

from asyncy.Stories import Stories
from asyncy.constants import ContextConstants
from asyncy.processing import Handler, Story

from pytest import mark, raises


def test_story_story(patch, app, logger):
    patch.init(Stories)
    story = Story.story(app, logger, 'story_name')
    Stories.__init__.assert_called_with(app, 'story_name', logger)
    assert isinstance(story, Stories)


@mark.asyncio
async def test_story_execute(patch, app, logger, story, async_mock):
    patch.object(Handler, 'run', new=async_mock(return_value=None))
    patch.object(Stories, 'first_line')
    story.prepare()
    await Story.execute(app, logger, story)
    assert Stories.first_line.call_count == 1
    logger.log.assert_called_with('story-execution', None)
    Handler.run.mock.assert_called_with(logger, Stories.first_line(), story)


@mark.asyncio
async def test_story_execute_calls_finish(patch, app, logger,
                                          story, async_mock):
    patch.object(Handler, 'run', new=async_mock(return_value=None))
    patch.object(Stories, 'first_line')
    io_loop = Mock()
    request = Mock()
    patch.object(io_loop, 'add_callback', side_effect=lambda x: x())
    context = {
        ContextConstants.server_io_loop: io_loop,
        ContextConstants.server_request: request
    }
    story.prepare(context=context)
    await Story.execute(app, logger, story)
    io_loop.add_callback.assert_called_once()
    request.finish.assert_called_once()


@mark.asyncio
async def test_story_run(patch, app, logger, async_mock):
    patch.object(time, 'time')
    patch.object(Story, 'execute', new=async_mock())
    patch.object(Story, 'story')
    await Story.run(app, logger, 'story_name')
    Story.story.assert_called_with(app, logger, 'story_name')
    Story.story.return_value.prepare.assert_called_with(None, None, None)
    Story.execute.mock.assert_called_with(app, logger, Story.story(),
                                          skip_server_finish=False)


@mark.asyncio
async def test_story_run_logger(patch, app, logger, async_mock):
    patch.object(Story, 'execute', new=async_mock())
    patch.object(Story, 'story')
    await Story.run(app, logger, 'story_name')
    assert logger.log.call_count == 2


@mark.asyncio
async def test_tasks_run_force_keyword(patch, app, logger, async_mock):
    patch.object(Story, 'execute', new=async_mock())
    patch.object(Story, 'story')
    with raises(TypeError):
        await Story.run(app, logger, 'story_name', 'story_id')


@mark.asyncio
async def test_story_run_with_id(patch, app, logger, async_mock):
    patch.object(Story, 'execute', new=async_mock())
    patch.object(Story, 'story')
    await Story.run(app, logger, 'story_name', story_id='story_id')


@mark.asyncio
async def test_story_run_prepare(patch, app, logger, async_mock):
    patch.object(Story, 'execute', new=async_mock())
    patch.object(Story, 'story')
    kwargs = {'start': 'start', 'block': 'block', 'context': 'context'}
    await Story.run(app, logger, 'story_name', **kwargs)
    Story.story().prepare.assert_called_with('context', 'start', 'block')
