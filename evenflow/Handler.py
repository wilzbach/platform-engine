# -*- coding: utf-8 -*-
from playhouse import db_url

from .Config import Config
from .models import db


class Handler:

    def init_db():
        db.init(db_url.parse(Config.get('database')))
