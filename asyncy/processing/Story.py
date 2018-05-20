# -*- coding: utf-8 -*-
import time

from .Handler import Handler
from ..Stories import Stories


class Story:

    @staticmethod
    def story(app, logger, story_name):
        return Stories(app, story_name, logger)

    @staticmethod
    def save(logger, story, start):
        """
        Saves the narration and the results for each line.
        """
        logger.log('story-save', story.name, story.app_id)

    @staticmethod
    def execute(app, logger, story):
        """
        Executes each line in the story
        """
        line_number = story.first_line()
        while line_number:
            line_number = Handler.run(logger, line_number, story)
            logger.log('story-execution', line_number)
            if line_number:
                if line_number.endswith('.story'):
                    line_number = Story.run(app, logger, line_number)

    @classmethod
    def run(cls, app, logger, story_name, *, story_id=None,
            start=None, block=None, context=None):
        logger.log('story-start', story_name, story_id)
        story = cls.story(app, logger, story_name)
        story.prepare(context, start, block)
        cls.execute(app, logger, story)
        logger.log('story-end', story_name, story_id)
