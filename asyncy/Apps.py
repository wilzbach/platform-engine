# -*- coding: utf-8 -*-
import psycopg2

from raven.contrib.tornado import AsyncSentryClient

from .Config import Config
from .Logger import Logger
from .App import App


class Apps:

    apps = {}

    @classmethod
    async def init_all(cls, sentry_dsn: str, release: str,
                       config: Config, logger: Logger):
        try:
            cls.sentry_client = AsyncSentryClient(
                dsn=sentry_dsn,
                release=release
            )

            conn = psycopg2.connect(database='asyncy', user='postgres',
                                    options=f'-c search_path=app_public')
            cur = conn.cursor()
            cur.execute(
                'with latest as (select app_uuid, max(id) as id '
                'from releases group by app_uuid) '
                'select app_uuid, id, config, payload '
                'from latest inner join releases '
                'using (app_uuid, id);')

            releases = cur.fetchall()

            for release in releases:
                # TODO:  validate in the db if this app is active
                app_id = release[0]
                version = release[1]
                environment = release[2]
                stories = release[3]

                services = {}  # TODO: loop through stories.services and gather intel from the db

                app = App(app_id, config, logger,
                          stories, services, environment,
                          sentry_client=cls.sentry_client)

                await app.bootstrap()
            
                cls.apps[app_id] = app
        except BaseException as e:
            logger.error('Failed to init!', exc=e)

    @classmethod
    def get(cls, app_id):
        return cls.apps[app_id]
