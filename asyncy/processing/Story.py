# -*- coding: utf-8 -*-
import time

from .Handler import Handler
from ..Stories import Stories


class Story:

    @staticmethod
    def story(logger, app_id, story_name):
        return Stories(logger, app_id, story_name)

    @staticmethod
    def save(config, logger, app, story, environment, start):
        """
        Saves the narration and the results for each line.
        """
        logger.log('story-save', story.filename, app.id)
        mongo = Handler.init_mongo(config.mongo)
        mongo_story = mongo.story(app.id, story.id)
        narration = mongo.narration(mongo_story, app.initial_data, environment,
                                    story.version, start,
                                    time.time())
        mongo.lines(narration, story.results)

    @staticmethod
    def execute(config, logger, app, story, environment):
        line_number = '1'
        while line_number:
            line_number = Handler.run(logger, line_number, story, environment)
            if line_number:
                if line_number.endswith('.story'):
                    line_number = Story.run(config, logger, app.id,
                                            line_number, app=app,
                                            parent_story=story)

    @classmethod
    def run(cls, config, logger, app_id, story_name, *, story_id=None):
        logger.log('story-start', story_name, app_id, story_id)
        start = time.time()
        story = cls.story(logger, app_id, story_name)
        story.get()
        cls.execute(config, logger, story)
        cls.save(config, logger, story, start)
        logger.log('story-end', story_name, app_id, story_id)
