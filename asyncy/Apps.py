# -*- coding: utf-8 -*-
import asyncio
import select
import sys
import threading

import psycopg2

from asyncy.Containers import Containers
from .App import App
from .Config import Config
from .GraphQLAPI import GraphQLAPI
from .Logger import Logger
from .Sentry import Sentry


class Apps:
    internal_services = ['http', 'log', 'crontab', 'file', 'event']
    apps = {}

    @classmethod
    def new_pg_conn(cls, config: Config):
        return psycopg2.connect(config.POSTGRES)

    @classmethod
    def get_releases(cls, config: Config):
        conn = cls.new_pg_conn(config)
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
    async def deploy_release(cls, config, logger, app_id, version, environment,
                             stories,
                             maintenance):
        logger.info(f'Deploying app {app_id}@{version}')
        if maintenance:
            logger.warn(f'Deployment halted {app_id}@{version}')
            return

        try:
            services = await cls.get_services(
                stories.get('yaml', {}), logger, stories)

            app = App(app_id, version, config, logger,
                      stories, services, environment)

            await Containers.clean_app(app)

            await app.bootstrap()

            cls.apps[app_id] = app
            logger.info(f'Successfully deployed app {app_id}@{version}')
        except BaseException as e:
            logger.error(
                f'Failed to bootstrap app {app_id}@{version}', exc=e)
            Sentry.capture_exc(e)

    @classmethod
    async def init_all(cls, sentry_dsn: str, release: str,
                       config: Config, logger: Logger):
        Sentry.init(sentry_dsn, release)

        releases = cls.get_releases(config)

        for release in releases:
            app_id = release[0]
            version = release[1]
            environment = release[2]
            stories = release[3]
            maintenance = release[4]
            await cls.deploy_release(config, logger, app_id, version,
                                     environment, stories, maintenance)

        loop = asyncio.get_event_loop()
        t = threading.Thread(target=cls.listen_to_releases,
                             args=[config, logger, loop],
                             daemon=True)
        t.start()

    @classmethod
    def get(cls, app_id: str):
        return cls.apps[app_id]

    @classmethod
    async def get_services(cls, asyncy_yaml, logger: Logger,
                           stories: dict):
        services = {}

        for service in stories.get('services', []):
            conf = asyncy_yaml.get('services', {}).get(service, {})
            # query the Hub for the OMG
            tag = conf.get('tag', 'latest')
            if conf.get('image'):
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
    async def destroy_app(cls, app: App, silent=False):
        app.logger.info(f'Destroying app {app.app_id}')
        try:
            await app.destroy()
        except BaseException as e:
            if not silent:
                raise e
            app.logger.error(
                f'Failed to destroy app {app.app_id}@{app.version}; '
                f'will eat exception (silent=True)',
                exc=e)

        app.logger.info(f'Completed destroying app {app.app_id}')
        cls.apps[app.app_id] = None

    @classmethod
    async def reload_app(cls, config: Config, logger: Logger, app_id: str):
        logger.info(f'Reloading app {app_id}')
        if cls.apps.get(app_id) is not None:
            await cls.destroy_app(cls.apps[app_id], silent=True)

        try:
            conn = cls.new_pg_conn(config)

            curs = conn.cursor()
            query = """
            with latest as (select app_uuid, max(id) as id
                from releases group by app_uuid)
            select app_uuid, id, config, payload, maintenance
            from latest
                   inner join releases using (app_uuid, id)
                   inner join apps on (latest.app_uuid = apps.uuid)
            where app_uuid = %s;
            """
            curs.execute(query, (app_id,))
            release = curs.fetchone()
            version = release[1]
            environment = release[2]
            stories = release[3]
            maintenance = release[4]
            await cls.deploy_release(config, logger, app_id, version,
                                     environment, stories, maintenance)
            logger.info(f'Reloaded app {app_id}@{version}')
        except BaseException as e:
            logger.error(
                f'Failed to reload app {app_id}', exc=e)
            Sentry.capture_exc(e)

    @classmethod
    async def destroy_all(cls):
        copy = cls.apps.copy()
        for app in copy.values():
            try:
                await cls.destroy_app(app)
            except BaseException as e:
                Sentry.capture_exc(e)

    @classmethod
    def listen_to_releases(cls, config: Config, logger: Logger, loop):
        logger.info('Listening for new releases...')
        conn = cls.new_pg_conn(config)
        conn.set_isolation_level(
            psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        curs = conn.cursor()
        curs.execute('listen release;')

        while True:
            if select.select([conn], [], [], 5) == ([], [], []):
                continue
            else:
                conn.poll()
                # TODO: poll throws an exception when the db connection breaks
                # TODO: We MUST terminate the engine so that it can restart.
                while conn.notifies:
                    notify = conn.notifies.pop(0)
                    asyncio.run_coroutine_threadsafe(
                        cls.reload_app(config, logger, notify.payload), loop)
