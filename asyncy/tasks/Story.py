# -*- coding: utf-8 -*-
import time

from .Handler import Handler
from ..models import Applications, Stories, db


class Story:

    @staticmethod
    def save(config, app, story, environment, start):
        """
        Saves the narration and the results for each line.
        """
        mongo = Handler.init_mongo(config.mongo)
        mongo_story = mongo.story(app.id, story.id)
        narration = mongo.narration(mongo_story, app.initial_data, environment,
                                    story.version, start,
                                    time.time())
        mongo.lines(narration, story.results)

    @classmethod
    def run(cls, config, logger, app_id, story_name, *, story_id=None):
        logger.log('task-start', app_id, story_name, story_id)
        db.from_url(config.database)
        app = Applications.get(Applications.id == app_id)
        story = app.get_story(story_name)
        story.build(app, config.github['app_identifier'],
                    config.github['pem_path'])
        environment = Handler.make_environment(story, app)
        start = time.time()
        context = {'application': app, 'story': story_name,
                   'results': {}, 'environment': environment}
        cls.execute(logger, app, story, context)
        cls.save(config, app, story, environment, start)

    @staticmethod
    def execute(logger, app, story, context):
        line_number = '1'
        while line_number:
            line_number = Handler.run(logger, line_number, story, context)
