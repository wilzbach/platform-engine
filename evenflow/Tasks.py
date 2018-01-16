# -*- coding: utf-8 -*-
from .Handler import Handler
from .models import Applications, Stories


class Tasks:

    @staticmethod
    def process_story(app_id, story_name, *, story_id=None):
        Handler.init_db()
        app = Applications.get(Applications.id == app_id)

        story = Stories.select()\
            .where(Stories.filename == story_name)\
            .where(Stories.application == app)
        Handler.build_story(story)

        line = '1'
        context = {}
        while line:
            line = Handler.run(line, context)
