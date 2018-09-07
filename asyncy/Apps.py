# -*- coding: utf-8 -*-
import psycopg2

from raven.contrib.tornado import AsyncSentryClient

from .App import App
from .Config import Config
from .GraphQLAPI import GraphQLAPI
from .Logger import Logger
from .Sentry import Sentry


class Apps:
    internal_services = ['http', 'log', 'crontab', 'file', 'event']
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
        cls._init_sentry(sentry_dsn, release)

        releases = cls.get_releases()

        for release in releases:
            app_id = release[0]
            version = release[1]
            environment = release[2]
            stories = release[3]
            maintenance = release[4]
            logger.info(f'Deploying app {app_id}@{version}')
            if maintenance:
                continue

            try:
                Sentry.clear_and_set_context(cls.sentry_client,
                                             app_id, version)

                services = await cls._prepare_services(
                    stories.get('yaml', {}), logger, stories)

                app = App(app_id, version, config, logger,
                          stories, services, environment,
                          sentry_client=cls.sentry_client)

                await app.bootstrap()

                cls.apps[app_id] = app
                logger.info(f'Successfully deployed app {app_id}@{version}')
            except BaseException as e:
                logger.error(
                    f'Failed to bootstrap app {app_id}@{version}', exc=e)
                cls.sentry_client.capture('raven.events.Exception')

    @classmethod
    def get(cls, app_id: str):
        return cls.apps[app_id]

    @classmethod
    async def _prepare_services(cls, asyncy_yaml, logger: Logger,
                                stories: dict):
        services = {}

        for service in stories.get('services', []):
            if service in cls.internal_services:
                continue

            conf = asyncy_yaml.get('services', {}).get(service, {})
            # query the Hub for the OMG
            tag = asyncy_yaml.get('tag', 'latest')
            if asyncy_yaml.get('image'):
                pull_url, omg = await GraphQLAPI.get_by_slug(
                    logger, conf['image'], tag)
            else:
                pull_url, omg = await GraphQLAPI.get_by_alias(
                    logger, service, tag)

            image = f'{pull_url}:{tag}'
            omg['image'] = image

            services[service] = {
                'tag': tag,
                'configuration': omg
            }

        return services

    @classmethod
    async def destroy_app(cls, app: App):
        app.logger.info(f'Destroying app {app.app_id}')
        await app.destroy()
        app.logger.info(f'Completed destroying app {app.app_id}')
        cls.apps[app.app_id] = None

    @classmethod
    async def destroy_all(cls):
        for app in cls.apps.values():
            await cls.destroy_app(app)
