# -*- coding: utf-8 -*-
import asyncio
import os
import select
import signal
import threading

import psycopg2

from .App import App
from .Config import Config
from .Containers import Containers
from .DeploymentLock import DeploymentLock
from .GraphQLAPI import GraphQLAPI
from .Logger import Logger
from .Sentry import Sentry
from .enums.ReleaseState import ReleaseState


class Apps:
    internal_services = ['http', 'log', 'crontab', 'file', 'event']

    deployment_lock = DeploymentLock()

    apps = {}
    """
    Keeps a reference to all apps. Keyed by their app_id,
    with their value being asyncy.App
    """

    @classmethod
    def new_pg_conn(cls, config: Config):
        return psycopg2.connect(config.POSTGRES)

    @classmethod
    def get_all_app_uuids_for_deployment(cls, config: Config):
        conn = cls.new_pg_conn(config)
        cur = conn.cursor()

        query = 'select app_uuid from releases group by app_uuid;'
        cur.execute(query)

        return cur.fetchall()

    @classmethod
    def update_release_state(cls, logger, config, app_id, version,
                             state: ReleaseState):
        conn = cls.new_pg_conn(config)
        cur = conn.cursor()
        query = 'update releases ' \
                'set state = %s ' \
                'where app_uuid = %s and id = %s;'
        cur.execute(query, (state.value, app_id, version))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f'Updated state for {app_id}@{version} to {state.name}')

    @classmethod
    async def deploy_release(cls, config, logger: Logger, app_id, app_dns,
                             version, environment, stories,
                             maintenance: bool, deleted: bool):
        logger.info(f'Deploying app {app_id}@{version}')
        if maintenance or deleted:
            cls.update_release_state(logger, config, app_id, version,
                                     ReleaseState.NO_DEPLOY)
            logger.warn(f'Deployment halted {app_id}@{version}; '
                        f'deleted={deleted}; maintenance={maintenance}')
            logger.warn(f'State changed to NO_DEPLOY for {app_id}@{version}')
            return

        cls.update_release_state(logger, config, app_id, version,
                                 ReleaseState.DEPLOYING)

        try:
            services = await cls.get_services(
                stories.get('yaml', {}), logger, stories)

            app = App(app_id, app_dns, version, config, logger,
                      stories, services, environment)

            await Containers.clean_app(app)

            await app.bootstrap()

            cls.apps[app_id] = app
            cls.update_release_state(logger, config, app_id, version,
                                     ReleaseState.DEPLOYED)

            logger.info(f'Successfully deployed app {app_id}@{version}')
        except BaseException as e:
            cls.update_release_state(logger, config, app_id, version,
                                     ReleaseState.FAILED)
            logger.error(
                f'Failed to bootstrap app {app_id}@{version}', exc=e)
            Sentry.capture_exc(e)

    @classmethod
    async def init_all(cls, sentry_dsn: str, release: str,
                       config: Config, logger: Logger):
        Sentry.init(sentry_dsn, release)

        releases = cls.get_all_app_uuids_for_deployment(config)

        # We must start listening for releases straight away,
        # before an app is even deployed.
        # If we start listening after all the apps are deployed,
        # then we might miss some notifications about releases.
        loop = asyncio.get_event_loop()
        t = threading.Thread(target=cls.listen_to_releases,
                             args=[config, logger, loop],
                             daemon=True)
        t.start()

        for release in releases:
            app_id = release[0]
            await cls.reload_app(config, logger, app_id)

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

            if '/' in service:
                pull_url, omg = await GraphQLAPI.get_by_slug(
                    logger, service, tag)
            else:
                pull_url, omg = await GraphQLAPI.get_by_alias(
                    logger, service, tag)

            if conf.get('image') is not None:
                image = f'{conf.get("image")}:{tag}'
            else:
                image = f'{pull_url}:{tag}'

            omg['image'] = image

            services[service] = {
                'tag': tag,
                'configuration': omg
            }

        return services

    @classmethod
    async def destroy_app(cls, app: App, silent=False,
                          update_db_state=False):
        app.logger.info(f'Destroying app {app.app_id}')
        try:
            if update_db_state:
                cls.update_release_state(app.logger, app.config, app.app_id,
                                         app.version,
                                         ReleaseState.TERMINATING)
            await app.destroy()
        except BaseException as e:
            if not silent:
                raise e
            app.logger.error(
                f'Failed to destroy app {app.app_id}@{app.version}; '
                f'will eat exception (silent=True)',
                exc=e)
        finally:
            if update_db_state:
                cls.update_release_state(app.logger, app.config, app.app_id,
                                         app.version,
                                         ReleaseState.TERMINATED)

        app.logger.info(f'Completed destroying app {app.app_id}')
        cls.apps[app.app_id] = None

    @classmethod
    async def reload_app(cls, config: Config, logger: Logger, app_id: str):
        logger.info(f'Reloading app {app_id}')
        if cls.apps.get(app_id) is not None:
            await cls.destroy_app(cls.apps[app_id], silent=True,
                                  update_db_state=True)

        can_deploy = False

        try:
            can_deploy = await cls.deployment_lock.try_acquire(app_id)
            if not can_deploy:
                logger.warn(f'Another deployment for app {app_id} is in '
                            f'progress. Will not reload.')
                return
            conn = cls.new_pg_conn(config)

            curs = conn.cursor()
            query = """
            with latest as (select app_uuid, max(id) as id
                            from releases
                            where state != 'NO_DEPLOY'::release_state
                            group by app_uuid)
            select app_uuid, id, config, payload, maintenance,
                   hostname, state, deleted
            from latest
                   inner join releases using (app_uuid, id)
                   inner join apps on (latest.app_uuid = apps.uuid)
                   inner join app_dns using (app_uuid)
            where app_uuid = %s;
            """
            curs.execute(query, (app_id,))
            release = curs.fetchone()
            version = release[1]
            environment = release[2]
            stories = release[3]
            maintenance = release[4]
            app_dns = release[5]
            state = release[6]
            deleted = release[7]
            if state == ReleaseState.FAILED.value:
                logger.warn(f'Cowardly refusing to deploy app '
                            f'{app_id}@{version} as it\'s '
                            f'last state is FAILED')
                return

            if stories is None:
                logger.info(f'No story found for deployment for '
                            f'app {app_id}@{version}. Halting deployment.')
                return
            await cls.deploy_release(
                config, logger, app_id, app_dns, version,
                environment, stories, maintenance, deleted)
            logger.info(f'Reloaded app {app_id}@{version}')
        except BaseException as e:
            logger.error(
                f'Failed to reload app {app_id}', exc=e)
            Sentry.capture_exc(e)
        finally:
            if can_deploy:
                # If we did acquire the lock, then we must release it.
                await cls.deployment_lock.release(app_id)

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
            try:
                if select.select([conn], [], [], 5) == ([], [], []):
                    continue
                else:
                    conn.poll()
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        asyncio.run_coroutine_threadsafe(
                            cls.reload_app(config, logger, notify.payload),
                            loop)
            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                logger.error('Connection to the DB has failed. Exiting.')
                # Because _thread.interrupt_main() doesn't work.
                os.kill(os.getpid(), signal.SIGINT)
                break
