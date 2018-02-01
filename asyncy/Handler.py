# -*- coding: utf-8 -*-
from .Config import Config
from .Containers import Containers
from .Lexicon import Lexicon
from .models import Results, db


class Handler:
    """
    Handles various task-related things.
    """

    @staticmethod
    def init_db():
        db.from_url(Config.get('database'))

    @staticmethod
    def init_mongo():
        return Results(Config.get('mongo'))

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
    def run(logger, line_number, story, context):
        """
        Run the story
        """
        line = story.line(line_number)
        args = story.resolve(logger, line_number)

        if line['method'] == 'if':
            return Lexicon.if_condition(line, args)

        container = Containers(line['container'])
        container.environment(context['application'], story)
        container.make_volume(story.filename)
        container.run(logger, *args)
        results = Handler.init_mongo()
        results.save(context['application'].name, context['story'],
                     container.result())
