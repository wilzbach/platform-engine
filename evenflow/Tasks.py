# -*- coding: utf-8 -*-
from playhouse import db_url

from .Config import Config
from .models import Applications, Stories, db


class Tasks:

    @staticmethod
    def process_story(app_id, story_name, *, story_id=None):
        db.init(db_url.parse(Config.get('database')))
        app = Applications.get(Applications.id == app_id)
        Stories.select()\
            .where(Stories.filename == story_name)\
            .where(Stories.application == app)
        return True
