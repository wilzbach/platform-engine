# -*- coding: utf-8 -*-
from .Config import Config
from .Containers import Containers
from .Lexicon import Lexicon
from .models import Mongo, db


class Handler:
    """
    Handles various task-related things.
    """

    @staticmethod
    def init_db():
        db.from_url(Config.get('database'))

    @staticmethod
    def init_mongo():
        return Mongo(Config.get('mongo'))

    @staticmethod
    def build_story(installation_id, story):
        """
        Build a storytree, given a story
        """
        app_identifier = Config.get('github.app_identifier')
        pem_path = Config.get('github.pem_path')
        story.backend(app_identifier, pem_path, installation_id)
        story.build_tree()

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
    def run(logger, line_number, story, context):
        """
        Run the story
        """
        line = story.line(line_number)
        command = story.resolve(logger, line_number)

        if line['method'] == 'if':
            return Lexicon.if_condition(line, command)

        container = Containers(line['container'])
        container.environment(story, context['application'])
        container.make_volume(story.filename)
        container.run(logger, command)
        context['results'][line_number] = container.result()
