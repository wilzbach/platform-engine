# -*- coding: utf-8 -*-
import psycopg2

from raven.contrib.tornado import AsyncSentryClient

from .Config import Config
from .Logger import Logger
from .App import App


class Apps:

    apps = {}
    sentry_client = None

    @classmethod
    def _init_sentry(cls, sentry_dsn: str, release: str):
        cls.sentry_client = AsyncSentryClient(
            dsn=sentry_dsn,
            release=release
        )

    @classmethod
    def get_releases(cls):
        conn = psycopg2.connect(database='asyncy', user='postgres',
                                options=f'-c search_path=app_public')
        cur = conn.cursor()

        query = """
        with latest as (select app_uuid, max(id) as id 
            from releases group by app_uuid)
        select app_uuid, id, config, payload, maintenance
        from latest
            inner join releases using (app_uuid, id)
            inner join apps on (releases.app_uuid = apps.uuid);
        """
        cur.execute(query)

        return cur.fetchall()

    @classmethod
    async def init_all(cls, sentry_dsn: str, release: str,
                       config: Config, logger: Logger):
        try:
            cls._init_sentry(sentry_dsn, release)

            releases = cls.get_releases()

            for release in releases:
                app_id = release[0]
                version = release[1]
                environment = release[2]
                stories = release[3]
                maintenance = release[4]
                if maintenance:
                    continue

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
