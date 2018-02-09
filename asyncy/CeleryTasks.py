# -*- coding: utf-8 -*-
from .CeleryApp import CeleryApp
from .Config import Config
from .Logger import Logger
from .Tasks import Tasks


config = Config()
logger = Logger(config)
logger.register()

app = CeleryApp.start(config)


@app.task
def run(app_id, story_name, story_id=None):
    Tasks.process_story(config, logger, app_id, story_name, story_id=story_id)
