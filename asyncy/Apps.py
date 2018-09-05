# -*- coding: utf-8 -*-
import os

from asyncy.Config import Config
from asyncy.Logger import Logger
from .App import App


class Apps:

    apps = {}

    @classmethod
    async def init_all(cls, config: Config, logger: Logger):
        app_ids = []  # TODO: read from db
        for app_id in app_ids:
            # TODO:  validate in the db if this app is active
            stories = {}  # TODO:
            environment = {}  # TODO:
            services = {}  # TODO:
            user_id = 'judepereira'  # TODO:
            sentry_dsn = ''  # TODO:
            release = '0.1'  # TODO:
            app = App(app_id, config, logger,
                      stories, services, environment,
                      beta_user_id=user_id, sentry_dsn=sentry_dsn,
                      release=release)

            cls.apps[app_id] = app

    @classmethod
    def get(cls, app_id):
        return cls.apps[app_id]
