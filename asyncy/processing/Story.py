# -*- coding: utf-8 -*-
import time

from .Handler import Handler
from ..Stories import Stories


class Story:

    @staticmethod
    def story(config, logger, app_id, story_name):
        return Stories(config, logger, app_id, story_name)

    @staticmethod
    def save(config, logger, story, start):
        """
        Saves the narration and the results for each line.
        """
        logger.log('story-save', story.name, story.app_id)
        mongo = Handler.init_mongo(config.mongo)
        mongo_story = mongo.story(story.name, story.app_id)
        narration = mongo.narration(mongo_story, story, story.version, start,
                                    time.time())
        mongo.lines(narration, story.results)

    @staticmethod
    def execute(config, logger, story):
        """
        Executes each line in the story
        """
        line_number = story.first_line()
        while line_number:
            line_number = Handler.run(logger, line_number, story)
            logger.log('story-execution', line_number)
            if line_number:
                if line_number.endswith('.story'):
                    line_number = Story.run(config, logger, story.app_id,
                                            line_number)

    @classmethod
    def run(cls, config, logger, app_id, story_name, *, story_id=None,
            block=None, environment=None, context=None):
        logger.log('story-start', story_name, app_id, story_id)
        start = time.time()
        story = cls.story(config, logger, app_id, story_name)
        story.get()
        if block:
            story.child_block(block)
        if environment:
            story.environment = environment
        if context:
            story.context = context
        cls.execute(config, logger, story)
        cls.save(config, logger, story, start)
        logger.log('story-end', story_name, app_id, story_id)
