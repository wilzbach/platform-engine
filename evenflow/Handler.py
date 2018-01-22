# -*- coding: utf-8 -*-
from playhouse import db_url

from storyscript import resolver

from .Config import Config
from .Containers import Containers
from .Lexicon import Lexicon
from .models import Results, database


class Handler:
    """
    Handles various task-related things.
    """

    @staticmethod
    def init_db():
        """
        Init the database
        """
        db_dict = db_url.parse(Config.get('database'))
        database.init(db_dict['database'], host=db_dict['host'],
                      port=db_dict['port'], user=db_dict['user'],
                      password=db_dict['password'])

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
    def run(line_number, line, data, context):
        """
        Run the story
        """
        args = resolver.resolve_obj(data, line['args'])

        if line['method'] == 'if':
            return Lexicon.if_condition(line, args)

        container = Containers(line['container'])
        container.run(*args)
        results = Handler.init_mongo()
        results.save(context['application'].name, context['story'],
                     container.result())
