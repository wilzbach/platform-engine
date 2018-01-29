# -*- coding: utf-8 -*-
from .CeleryApp import CeleryApp
from .Logger import Logger
from .Tasks import Tasks


logger = Logger()

app = CeleryApp.start()


@app.task
def run(app_id, story_name, story_id=None):
    Tasks.process_story(app_id, story_name, story_id=story_id)
