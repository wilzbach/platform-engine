# -*- coding: utf-8 -*-
from asyncy.App import App
from asyncy.Config import Config
from asyncy.Containers import Containers
from asyncy.processing import Story

from pytest import mark


@mark.asyncio
async def test_story_run(patch, logger, story, async_mock):
    app = App(Config(), logger)
    story.app = app
    patch.object(Story, 'story', return_value=story)
    patch.object(Containers, 'format_command',
                 new=async_mock(return_value=['pwd']))
    await Story.run(app, logger, story_name='echo.story')
