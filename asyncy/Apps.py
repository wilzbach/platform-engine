# -*- coding: utf-8 -*-
from raven.contrib.tornado import AsyncSentryClient

from asyncy.Config import Config
from asyncy.Logger import Logger
from .App import App


class Apps:

    apps = {}

    @classmethod
    async def init_all(cls, sentry_dsn: str, release: str,
                       config: Config, logger: Logger):
        cls.sentry_client = AsyncSentryClient(
            dsn=sentry_dsn,
            release=release
        )

        app_ids = []  # TODO: read from db
        for app_id in app_ids:
            # TODO:  validate in the db if this app is active
            stories = {}  # TODO:
            environment = {}  # TODO:
            services = {}  # TODO:
            user_id = 'judepereira'  # TODO:
            app = App(app_id, config, logger,
                      stories, services, environment,
                      beta_user_id=user_id, sentry_client=cls.sentry_client)

            cls.apps[app_id] = app

    @classmethod
    def get(cls, app_id):
        return cls.apps[app_id]
