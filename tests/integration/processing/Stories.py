# -*- coding: utf-8 -*-
from asyncy.App import App
from asyncy.Config import Config
from asyncy.Containers import Containers
from asyncy.processing import Stories

from pytest import mark


# @mark.asyncio
# async def test_story_run(patch, logger, story, app):
#     app.config = Config()
#     story.app = app
#     story.app.app_id = 'app_id'
#     patch.object(Stories, 'story', return_value=story)
#     patch.object(Containers, 'format_command', return_value=['pwd'])
#     await Stories.run(app, logger, story_name='hello.story')
