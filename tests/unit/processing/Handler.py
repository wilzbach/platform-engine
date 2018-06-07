# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from asyncy.processing import Handler, Lexicon

from pytest import mark


@mark.asyncio
async def test_handler_run(patch, logger, story):
    patch.many(story, ['line', 'start_line'])
    await Handler.run(logger, '1', story)
    story.line.assert_called_with('1')
    story.start_line.assert_called_with('1')


@mark.asyncio
async def test_handler_run_run(patch, logger, story, async_mock):
    patch.object(Lexicon, 'execute', new=async_mock(return_value=MagicMock()))
    Lexicon.execute.return_value = MagicMock()
    patch.object(story, 'line', return_value={'method': 'execute'})
    result = await Handler.run(logger, '1', story)
    Lexicon.execute.mock.assert_called_with(logger, story, story.line())
    assert result == Lexicon.execute.mock.return_value


@mark.asyncio
async def test_handler_run_set(patch, logger, story):
    patch.object(Lexicon, 'set')
    patch.object(story, 'line', return_value={'method': 'set'})
    result = await Handler.run(logger, '1', story)
    Lexicon.set.assert_called_with(logger, story, story.line())
    assert result == Lexicon.set()


@mark.asyncio
async def test_handler_run_if(patch, logger, story):
    patch.object(Lexicon, 'if_condition')
    patch.object(story, 'line', return_value={'method': 'if'})
    result = await Handler.run(logger, '1', story)
    Lexicon.if_condition.assert_called_with(logger, story, story.line())
    assert result == Lexicon.if_condition()


@mark.asyncio
async def test_handler_run_for(patch, logger, story, async_mock):
    patch.object(Lexicon, 'for_loop', new=async_mock())
    patch.object(story, 'line', return_value={'method': 'for'})
    result = await Handler.run(logger, 1, story)
    Lexicon.for_loop.mock.assert_called_with(logger, story, story.line())
    assert result == Lexicon.for_loop.mock.return_value
