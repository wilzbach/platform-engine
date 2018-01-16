# -*- coding: utf-8 -*-
from playhouse import db_url

from .Config import Config
from .models import db


class Handler:

    @staticmethod
    def init_db():
        db.init(db_url.parse(Config.get('database')))

    @staticmethod
    def build_story(story):
        app_identifier = Config.get('github.app_identifier')
        pem_path = Config.get('github.pem_path')
        story.provider(app_identifier, pem_path)
        story.build_tree()
