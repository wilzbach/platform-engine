# -*- coding: utf-8 -*-
from .CeleryApp import CeleryApp
from .Config import Config
from .Logger import Logger
from .tasks import Story


config = Config()
logger = Logger(config)
logger.register()

app = CeleryApp.start(config)


@app.task
def process_story(app_id, story_name, story_id=None):
    Story.run(config, logger, app_id, story_name, story_id=story_id)
