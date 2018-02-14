# -*- coding: utf-8 -*-
from ..Containers import Containers
from ..Lexicon import Lexicon
from ..models import Mongo


class Handler:
    """
    Handles various task-related things.
    """

    @staticmethod
    def init_mongo(mongo_url):
        return Mongo(mongo_url)

    @staticmethod
    def make_environment(story, application):
        """
        Makes the environment from story and application.
        """
        environment = story.environment()
        application_environment = application.environment()
        for key, value in environment.items():
            if key in application_environment:
                environment[key] = application_environment[key]
        return environment

    @staticmethod
    def run(logger, line_number, story, environment):
        """
        Run the story
        """
        story.start_line(line_number)
        line = story.line(line_number)
        command = story.resolve(logger, line_number)

        if line['method'] == 'if':
            return Lexicon.if_condition(line, command)
        elif line['method'] == 'next':
            return Lexicon.next(command)

        container = Containers(line['container'])
        container.make_volume(story.filename)
        container.run(logger, command, environment)
        story.end_line(line_number, container.result())
