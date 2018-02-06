# -*- coding: utf-8 -*-
import time

from .Handler import Handler
from .models import Applications, Stories


class Tasks:

    @staticmethod
    def process_story(logger, app_id, story_name, *, story_id=None):
        logger.log('task-start', app_id, story_name, story_id)
        Handler.init_db()
        app = Applications.get(Applications.id == app_id)
        story = app.get_story(story_name)
        story.data(app.initial_data)
        Handler.build_story(app.user.installation_id, story)

        line_number = '1'
        context = {'application': app, 'story': story_name,
                   'start': time.time(), 'results': {}}
        while line_number:
            line_number = Handler.run(logger, line_number, story, context)
