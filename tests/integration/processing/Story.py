# -*- coding: utf-8 -*-
from asyncy.App import App
from asyncy.Config import Config
from asyncy.Containers import Containers
from asyncy.processing.Services import Services
from asyncy.processing import Story
from asyncio import Future
from pytest import mark

@mark.asyncio
async def test_story_run(patch, config, logger, bad_story, app, async_mock):
    # story.app = app
    # story.app.app_id = 'app_id'
    # patch.object(Story, 'story', return_value=story)
    # patch.object(Containers, 'format_command', return_value=['pwd'])

    patch.object(Services, 'execute', new=async_mock(return_value="Goodbye World"))
    patch.object(Services, 'start_container', new=async_mock(return_value="asdf"))

    await Story.execute(logger, bad_story)
    assert True

# @mark.asyncio
# async def test_story_run(patch, logger, story, app):
#     app.config = Config()
#     story.app = app
#     story.app.app_id = 'app_id'
#     patch.object(Story, 'story', return_value=story)
#     patch.object(Containers, 'format_command', return_value=['pwd'])
#     await Story.run(app, logger, story_name='hello.story')
