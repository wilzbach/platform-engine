# -*- coding: utf-8 -*-
from pytest import mark

from storyruntime.App import App
from storyruntime.Config import Config
from storyruntime.Containers import Containers
from storyruntime.processing import Stories


# @mark.asyncio
# async def test_story_run(patch, logger, story, app):
#     app.config = Config()
#     story.app = app
#     story.app.app_id = 'app_id'
#     patch.object(Stories, 'story', return_value=story)
#     patch.object(Containers, 'format_command', return_value=['pwd'])
#     await Stories.run(app, logger, story_name='hello.story')
