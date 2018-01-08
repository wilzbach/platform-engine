# -*- coding: utf-8 -*-
from playhouse import db_url

from .Config import Config
from .models import Applications, db


class Tasks:

    @staticmethod
    def process_story(app_id, story_name, *, story_id=None):
        db.init(db_url.parse(Config.get('database')))
        Applications.get(Applications.id == app_id)
        return True
