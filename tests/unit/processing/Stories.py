# -*- coding: utf-8 -*-
import collections
import time
from unittest import mock

import pytest
from pytest import mark

from storyruntime import Metrics
from storyruntime.Containers import Containers
from storyruntime.Exceptions import StoryscriptError, StoryscriptRuntimeError
from storyruntime.Story import Story
from storyruntime.constants import ContextConstants
from storyruntime.constants.LineSentinels import LineSentinels
from storyruntime.processing import Lexicon, Stories
from storyruntime.utils import Dict


def test_stories_story(patch, app, logger):
    patch.init(Story)
    story = Stories.story(app, logger, 'story_name')
    Story.__init__.assert_called_with(app, 'story_name', logger)
    assert isinstance(story, Story)


@mark.asyncio
async def test_stories_execute(patch, app, logger, story, async_mock):
    patch.object(Stories, 'execute_line', new=async_mock(return_value=None))
    patch.object(Story, 'first_line')
    story.prepare()
    await Stories.execute(logger, story)
    assert Story.first_line.call_count == 1
    logger.log.assert_called_with('story-execution', None)
    Stories.execute_line.mock.assert_called_with(logger,
                                                 story, Story.first_line())


@mark.asyncio
async def test_stories_execute_escaping_sentinel(patch, app, logger,
                                                 story, async_mock):
    """
    This one ensures that any uncaught sentinels result in an exception.
    """
    patch.object(Stories, 'execute_line', new=async_mock(
        return_value=LineSentinels.RETURN))
    patch.object(Story, 'first_line')
    story.prepare()
    with pytest.raises(StoryscriptRuntimeError):
        await Stories.execute(logger, story)


@mark.asyncio
async def test_stories_execute_line_unknown_method(logger, story):
    story.tree['1']['method'] = 'foo_method'
    with pytest.raises(StoryscriptError):
        await Stories.execute_line(logger, story, '1')


Method = collections.namedtuple('Method', 'name lexicon_name async_mock')


@mark.parametrize('method', [
    Method(name='if', lexicon_name='if_condition', async_mock=True),
    Method(name='elif', lexicon_name='if_condition', async_mock=True),
    Method(name='else', lexicon_name='if_condition', async_mock=True),
    Method(name='for', lexicon_name='for_loop', async_mock=True),
    Method(name='execute', lexicon_name='execute', async_mock=True),
    Method(name='set', lexicon_name='set', async_mock=True),
    Method(name='function', lexicon_name='function', async_mock=True),
    Method(name='call', lexicon_name='call', async_mock=True),
    Method(name='when', lexicon_name='when', async_mock=True),
    Method(name='return', lexicon_name='ret', async_mock=True),
    Method(name='break', lexicon_name='break_', async_mock=True)
])
@mark.asyncio
async def test_stories_execute_line_generic(patch, logger, story,
                                            async_mock, method):
    patch.object(Lexicon, method.lexicon_name, new=async_mock())

    patch.object(story, 'line', return_value={'method': method.name})
    patch.many(story, ['start_line', 'new_frame'])
    result = await Stories.execute_line(logger, story, '1')

    story.new_frame.assert_called_with('1')

    mock = getattr(Lexicon, method.lexicon_name)
    if method.async_mock:
        mock = mock.mock

    mock.assert_called_with(logger, story, story.line.return_value)
    assert result == mock.return_value

    story.line.assert_called_with('1')
    story.start_line.assert_called_with('1')


@mark.asyncio
@mark.parametrize('line_4_result', ['5', LineSentinels.RETURN,
                                    LineSentinels.BREAK])
async def test_stories_execute_block(patch, logger, story,
                                     async_mock, line_4_result):
    story.tree = {
        '1': {'ln': '1', 'next': '2'},
        '2': {'ln': '2', 'next': '3', 'enter': '3',
              'output': ['foo_client'], 'method': 'when'},
        '3': {'ln': '3', 'next': '4', 'parent': '2'},
        '4': {'ln': '4', 'next': '5', 'parent': '2'},
        '5': {'ln': '5', 'next': '6', 'parent': '2'},
        '6': {'ln': '6', 'parent': '1'}
    }

    patch.object(Stories, 'execute_line', new=async_mock(
        side_effect=['4', line_4_result, '6']))

    line = story.line
    story.context = {
        ContextConstants.service_event: {'data': {'foo': 'bar'}}
    }

    def proxy_line(*args):
        return line(*args)

    patch.object(story, 'line', side_effect=proxy_line)

    execute_block_return = await Stories.execute_block(
        logger, story, story.tree['2'])

    assert story.context[ContextConstants.service_output] == 'foo_client'
    assert story.context['foo_client'] \
        == story.context[ContextConstants.service_event]['data']

    if LineSentinels.is_sentinel(line_4_result):
        assert [
            mock.call(logger, story, '3'),
            mock.call(logger, story, '4')
        ] == Stories.execute_line.mock.mock_calls
        assert [
            mock.call('3'),
            mock.call('4')
        ] == story.line.mock_calls
        if line_4_result == LineSentinels.RETURN:
            assert execute_block_return is None
        else:
            assert execute_block_return == line_4_result
    else:
        assert [
            mock.call(logger, story, '3'),
            mock.call(logger, story, '4'),
            mock.call(logger, story, '5')
        ] == Stories.execute_line.mock.mock_calls
        assert [
            mock.call('3'),
            mock.call('4'),
            mock.call('5'),
            mock.call('6'),
            mock.call('1')
        ] == story.line.mock_calls


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

    Metrics.story_run_failure.labels\
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
    patch.object(Stories, 'execute_block', new=async_mock())
    patch.object(Stories, 'story')
    block = '1'
    await Stories.run(app, logger, 'story_name',
                      context='context', block=block)
    Stories.story().prepare.assert_called_with('context')
    Stories.story().line.assert_called_with(block)
    Stories.story().new_frame.assert_called_with(block)
    Stories.execute_block.mock \
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


@mark.asyncio
async def test_stories_execute_does_not_wrap(patch, story, async_mock):
    def exc(*args):
        raise StoryscriptError()

    patch.object(Lexicon, 'execute', new=async_mock(side_effect=exc))
    patch.object(story, 'line', return_value={'method': 'execute'})
    with pytest.raises(StoryscriptError):
        await Stories.execute_line(story.logger, story, '10')
