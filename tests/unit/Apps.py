# -*- coding: utf-8 -*-
import asyncio
import os
from unittest import mock

import pytest
from pytest import fixture, mark

from storyruntime.App import App, AppData
from storyruntime.AppConfig import AppConfig
from storyruntime.Apps import Apps
from storyruntime.Containers import Containers
from storyruntime.Exceptions import StoryscriptError, TooManyActiveApps, \
    TooManyServices, TooManyVolumes
from storyruntime.GraphQLAPI import GraphQLAPI
from storyruntime.Kubernetes import Kubernetes
from storyruntime.Logger import Logger
from storyruntime.ServiceUsage import ServiceUsage
from storyruntime.constants import Events
from storyruntime.constants.ServiceConstants import ServiceConstants
from storyruntime.db.Database import Database
from storyruntime.entities.Release import Release
from storyruntime.entities.ReportingEvent import ReportingEvent
from storyruntime.enums.AppEnvironment import AppEnvironment
from storyruntime.enums.ReleaseState import ReleaseState
from storyruntime.reporting.Reporter import Reporter


def exc():
    def foo(*args, **kwargs):
        raise Exception()

    return foo


def asyncio_timeout_exc():
    def foo(*args, **kwargs):
        raise asyncio.TimeoutError()

    return foo


def asyncy_exc():
    def foo(*args, **kwargs):
        raise StoryscriptError()

    return foo


@fixture
def db(patch, magic, async_cm_mock, async_mock):
    con = magic()
    patch.object(con, 'add_listener', new=async_mock())
    patch.object(con, 'close', new=async_mock())
    con.con = con
    return con


@mark.asyncio
async def test_listen_to_releases(patch, db, magic,
                                  config, logger, async_mock):
    patch.object(Database, 'new_con', new=async_mock(return_value=db))
    patch.many(asyncio, ['run_coroutine_threadsafe', 'create_task'])
    patch.object(Apps, 'reload_app')

    loop = magic()

    await Apps.listen_to_releases(config, logger, loop)

    Database.new_con.mock.assert_called_once()
    db.con.add_listener.mock.assert_called_once()

    patch.many(os, ['kill', 'getpid'])
    patch.object(Apps, 'release_listener_db_con', side_effect=db)
    patch.object(db.con, 'add_listener',
                 new=async_mock(side_effect=OSError))

    await Apps.listen_to_releases(config, logger, loop)
    asyncio.create_task \
        .assert_called_with(Apps.release_listener_db_con.close())
    os.kill.assert_called_once()
    os.getpid.assert_called_once()


@mark.asyncio
async def test_supervise_listener(patch, db, magic,
                                  config, logger, async_mock):
    loop = magic()
    patch.object(Apps, 'listen_to_releases', new=async_mock())
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(Apps.start_release_listener(config,
                                                           logger, loop),
                               timeout=3.2)
    assert Apps.listen_to_releases.mock.call_count == 4

    patch.object(Apps, 'release_listener_db_con')
    patch.object(Apps.release_listener_db_con, '_con', True)
    patch.object(Apps.release_listener_db_con, '_listeners', {'release'})

    Apps.listen_to_releases.mock.call_count = 0
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(Apps.start_release_listener(config,
                                                           logger, loop),
                               timeout=1.2)
    assert Apps.listen_to_releases.mock.call_count == 0


@mark.asyncio
async def test_destroy_all(patch, async_mock, magic):
    patch.object(Containers, 'clean_app', new=async_mock())
    app = magic()
    app.destroy = async_mock()
    Apps.apps = {'app_id': app}
    app.app_id = 'app_id'
    await Apps.destroy_all()
    app.destroy.mock.assert_called()
    assert Apps.apps['app_id'] is None
    Containers.clean_app.mock.assert_called()


@mark.asyncio
async def test_destroy_all_exc(patch, async_mock, magic):
    app = magic()
    patch.object(Reporter, 'capture_evt')
    patch.object(ReportingEvent, 'from_release')

    err = BaseException()

    async def exc():
        raise err

    app.destroy = exc
    Apps.apps = {'app_id': app}
    app.app_id = 'app_id'
    app.app_name = 'app_name'
    app.logger = magic()
    await Apps.destroy_all()

    ReportingEvent.from_release.assert_called_with(
        app.release, 'App Destroy Failed', exc_info=err)

    Reporter.capture_evt.assert_called_with(
        ReportingEvent.from_release.return_value)


@mark.asyncio
@mark.parametrize('app_environment', ['STAGING', 'PRODUCTION', 'DEV'])
async def test_init_all(app_environment, patch, magic,
                        async_mock, config, logger, db):
    config.APP_ENVIRONMENT = AppEnvironment[app_environment]
    db()
    apps = [{
        'uuid': 'my_app_uuid'
    }]
    patch.object(Database, 'get_all_app_uuids_for_deployment',
                 new=async_mock(return_value=apps))
    patch.object(Apps, 'reload_app', new=async_mock())
    patch.object(Apps, 'start_release_listener')
    patch.object(ServiceUsage, 'start_metrics_recorder')
    patch.object(asyncio, 'create_task')

    await Apps.init_all(config, logger)
    Apps.reload_app.mock.assert_called_with(
        config, logger, 'my_app_uuid')

    loop = asyncio.get_event_loop()

    assert asyncio.create_task.mock_calls == [
        mock.call(Apps.start_release_listener(config, logger, loop)),
    ] + ([
        mock.call(ServiceUsage.start_metrics_recorder(config, logger))
    ] if config.APP_ENVIRONMENT == AppEnvironment.PRODUCTION else [])


def test_get(magic):
    app = magic()
    Apps.apps['app_id'] = app
    assert Apps.get('app_id') == app


@mark.asyncio
async def test_reload_app_ongoing_deployment(config, logger, patch):
    app_id = 'my_app'
    patch.object(Database, 'pg_pool')

    await Apps.deployment_lock.try_acquire(app_id)

    await Apps.reload_app(config, logger, app_id)

    logger.warn.assert_called()
    Database.pg_pool.assert_not_called()


@mark.asyncio
async def test_reload_app_no_story(patch, config, logger, db, async_mock):
    app_id = 'app_id'
    app_name = 'app_name'

    patch.object(Apps, 'destroy_app', new=async_mock())
    patch.object(Apps, 'deploy_release', new=async_mock())

    release = Release(
        app_uuid=app_id,
        app_name=app_name,
        version=1,
        environment={},
        stories=None,
        maintenance=False,
        always_pull_images=False,
        app_dns='app_dns',
        state='QUEUED',
        deleted=True,
        owner_uuid='owner_uuid',
        owner_email='owner_email',
        app_environment=AppEnvironment.PRODUCTION
    )
    patch.object(Database, 'get_release_for_deployment',
                 new=async_mock(return_value=release))

    await Apps.reload_app(config, logger, app_id)

    Apps.deploy_release.mock.assert_not_called()


@mark.parametrize('raise_exc', [None, exc, asyncio_timeout_exc])
@mark.parametrize('previous_state', [
    'QUEUED', 'FAILED', 'TEMP_DEPLOYMENT_FAILURE'
])
@mark.parametrize('app_environment_db', ['STAGING', 'PRODUCTION', 'DEV'])
@mark.parametrize('app_environment_config', ['STAGING', 'PRODUCTION', 'DEV'])
@mark.asyncio
async def test_reload_app(patch, config, logger, db, async_mock,
                          magic, raise_exc, previous_state,
                          app_environment_db, app_environment_config):
    config.APP_ENVIRONMENT = AppEnvironment[app_environment_config]
    old_app = magic()
    app_id = 'app_id'
    app_name = 'app_name'
    app_dns = 'app_dns'
    Apps.apps = {app_id: old_app}
    patch.object(Reporter, 'capture_evt')
    patch.object(ReportingEvent, 'from_release')
    app_logger = magic()
    patch.object(Apps, 'make_logger_for_app', return_value=app_logger)
    patch.object(Database, 'update_release_state', new=async_mock())

    patch.object(Apps, 'destroy_app', new=async_mock())
    if raise_exc:
        patch.object(Apps, 'deploy_release',
                     new=async_mock(side_effect=raise_exc()))
    else:
        patch.object(Apps, 'deploy_release', new=async_mock())

    release = Release(
        app_uuid=app_id,
        app_name=app_name,
        version=1,
        environment={},
        stories={},
        maintenance=False,
        always_pull_images=False,
        app_dns=app_dns,
        state=previous_state,
        deleted=True,
        owner_uuid='owner_uuid',
        owner_email='example@example.com',
        app_environment=AppEnvironment[app_environment_db]
    )

    patch.object(Database, 'get_release_for_deployment',
                 new=async_mock(return_value=release))

    await Apps.reload_app(config, logger, app_id)

    Apps.destroy_app.mock.assert_called_with(old_app, silent=True,
                                             update_db_state=True)

    if AppEnvironment[app_environment_db] != \
            AppEnvironment[app_environment_config]:
        Apps.deploy_release.mock.assert_not_called()
        logger.info.assert_called()
        logger.error.assert_not_called()
        logger.warn.assert_not_called()
        Database.update_release_state.mock.assert_not_called()
        return

    if previous_state == 'FAILED':
        Apps.deploy_release.mock.assert_not_called()
        logger.warn.assert_called()
        logger.error.assert_not_called()
        Database.update_release_state.mock.assert_not_called()
        return

    Apps.deploy_release.mock.assert_called_with(
        config=config, release=release
    )

    if raise_exc:
        logger.error.assert_called()
        assert ReportingEvent.from_release.mock_calls[0][1][0] == release
        assert ReportingEvent.from_release.mock_calls[0][1][
            1] == Events.APP_RELOAD_FAILED
        assert isinstance(
            ReportingEvent.from_release.mock_calls[0][2]['exc_info'],
            BaseException)

        Reporter.capture_evt.assert_called_with(
            ReportingEvent.from_release.return_value)
    else:
        logger.error.assert_not_called()

    if raise_exc == asyncio_timeout_exc:
        Database.update_release_state.mock.assert_called_with(
            app_logger, config, 'app_id', 1, ReleaseState.TIMED_OUT)


@mark.asyncio
async def test_deploy_release_many_services(patch, async_mock):
    patch.object(Apps, 'make_logger_for_app')
    patch.object(Database, 'update_release_state', new=async_mock())
    patch.init(TooManyServices)
    patch.object(TooManyServices, '__str__', return_value='too_many_services')

    stories = {'services': {}}

    for i in range(20):
        stories['services'][f'service_{i}'] = {}

    await Apps.deploy_release(
        config={},
        release=Release(
            app_uuid='app_id',
            app_name='app_name',
            version='app_version',
            environment={},
            stories=stories,
            maintenance=False,
            always_pull_images=False,
            app_dns='app_dns',
            state='QUEUED',
            deleted=False,
            owner_uuid='owner_uuid',
            owner_email='example@example.com',
            app_environment=AppEnvironment.PRODUCTION
        )
    )

    TooManyServices.__init__.assert_called_with(20, 15)
    Database.update_release_state.mock.assert_called()


@mark.asyncio
async def test_deploy_release_many_apps(patch, magic, async_mock):
    patch.object(Apps, 'make_logger_for_app')
    patch.object(Database, 'update_release_state', new=async_mock())
    patch.init(TooManyActiveApps)
    patch.object(TooManyActiveApps, '__str__', return_value='too_many')

    stories = {'services': {}}
    Apps.apps = {}

    try:
        for i in range(20):
            Apps.apps[f'app_{i}'] = magic()
            Apps.apps[f'app_{i}'].owner_uuid = 'owner_uuid'
            stories['services'][f'service_{i}'] = {}

        await Apps.deploy_release(config={}, release=Release(
            app_uuid='app_id',
            app_name='app_name',
            version='app_version',
            environment={},
            stories=stories,
            maintenance=False,
            always_pull_images=False,
            app_dns='app_dns',
            state='QUEUED',
            deleted=False,
            owner_uuid='owner_uuid',
            owner_email='example@example.com',
            app_environment=AppEnvironment.PRODUCTION
        ))

        TooManyActiveApps.__init__.assert_called_with(20, 5)
        Database.update_release_state.mock.assert_called()
    finally:
        Apps.apps = {}  # Cleanup.


def test_get_app_config(patch):
    patch.init(AppConfig)
    raw = {'raw': 1}
    ret = Apps.get_app_config(raw)
    assert isinstance(ret, AppConfig)
    AppConfig.__init__.assert_called_with(raw)


@mark.asyncio
async def test_deploy_release_many_volumes(patch, async_mock):
    patch.object(Apps, 'make_logger_for_app')
    patch.object(Database, 'update_release_state', new=async_mock())
    patch.init(TooManyVolumes)
    patch.object(TooManyVolumes, '__str__', return_value='too_many_vols')

    stories = {'services': {}}

    for i in range(10):
        stories['services'][f'service_{i}'] = {
            ServiceConstants.config: {
                'volumes': {
                    'a': {},
                    'b': {}
                }
            }
        }

    patch.object(Apps, 'get_services',
                 new=async_mock(return_value=stories['services']))
    await Apps.deploy_release(
        config={},
        release=Release(
            app_uuid='app_id',
            app_name='app_name',
            version='app_version',
            environment={},
            stories=stories,
            maintenance=False,
            always_pull_images=False,
            app_dns='app_dns',
            state='QUEUED',
            deleted=False,
            owner_uuid='owner_uuid',
            owner_email='owner_email',
            app_environment=AppEnvironment.PRODUCTION
        )
    )

    TooManyVolumes.__init__.assert_called_with(20, 15)
    Database.update_release_state.mock.assert_called()


@mark.parametrize('raise_exc', [None, exc, asyncy_exc])
@mark.parametrize('maintenance', [True, False])
@mark.parametrize('always_pull_images', [True, False])
@mark.parametrize('deleted', [True, False])
@mark.asyncio
async def test_deploy_release(config, magic, patch, deleted,
                              async_mock, raise_exc, maintenance,
                              always_pull_images):
    patch.object(Reporter, 'capture_evt')
    patch.object(ReportingEvent, 'from_release')
    patch.object(Kubernetes, 'clean_namespace', new=async_mock())
    patch.object(Containers, 'init', new=async_mock())
    patch.object(Database, 'update_release_state', new=async_mock())
    app_logger = magic()
    patch.object(Apps, 'make_logger_for_app', return_value=app_logger)
    Apps.apps = {}
    services = magic()

    app_config = magic()
    patch.object(Apps, 'get_app_config', return_value=app_config)

    patch.object(Apps, 'get_services', new=async_mock(return_value=services))
    patch.init(App)
    if raise_exc is not None:
        patch.object(App, 'bootstrap', new=async_mock(side_effect=raise_exc()))
    else:
        patch.object(App, 'bootstrap', new=async_mock())

    release = Release(
        app_uuid='app_id',
        app_name='app_name',
        version='version',
        environment={'env': True},
        stories={'stories': True},
        maintenance=maintenance,
        always_pull_images=always_pull_images,
        app_dns='app_dns',
        state='QUEUED',
        deleted=deleted,
        owner_uuid='owner_uuid',
        owner_email='owner_email',
        app_environment=AppEnvironment.PRODUCTION
    )

    await Apps.deploy_release(config=config, release=release)

    if maintenance:
        assert Database.update_release_state.mock.call_count == 0
        app_logger.warn.assert_called()
    elif deleted:
        app_logger.warn.assert_called()
        Database.update_release_state.mock.assert_called_with(
            app_logger, config, 'app_id', 'version', ReleaseState.NO_DEPLOY)
    else:
        assert Database.update_release_state.mock.mock_calls[0] == mock.call(
            app_logger, config, 'app_id', 'version', ReleaseState.DEPLOYING)

        App.__init__.assert_called_with(app_data=AppData(
            release=release,
            config=config,
            logger=app_logger,
            services=services,
            app_config=app_config
        ))

        App.bootstrap.mock.assert_called()
        Containers.init.mock.assert_called()
        assert Apps.apps.get('app_id') is not (raise_exc is None)
        if raise_exc == exc:
            # ReportingEvent.from_release.assert_called_with(
            #     app.release, 'App Destroy Failed', exc_info=err)

            Reporter.capture_evt.assert_called_with(
                ReportingEvent.from_release.return_value)
            assert \
                Database.update_release_state.mock.mock_calls[1] \
                == mock.call(app_logger, config, 'app_id', 'version',
                             ReleaseState.TEMP_DEPLOYMENT_FAILURE)
        elif raise_exc == asyncy_exc:
            assert \
                Database.update_release_state.mock.mock_calls[1] \
                == mock.call(app_logger, config, 'app_id',
                             'version', ReleaseState.FAILED)
        else:
            assert \
                Database.update_release_state.mock.mock_calls[1] \
                == mock.call(app_logger, config,
                             'app_id', 'version', ReleaseState.DEPLOYED)


def test_make_logger_for_app(patch, config):
    patch.many(Logger, ['start', 'adapt'])
    logger = Apps.make_logger_for_app(config, 'my_awesome_app', '17.1')
    logger.start.assert_called()
    logger.adapt.assert_called_with('my_awesome_app', '17.1')


@mark.asyncio
async def test_get_services(patch, logger, async_mock):
    patch.object(GraphQLAPI, 'get_by_slug',
                 new=async_mock(return_value=('slug_uuid', 'slug_pull',
                                              {'slug': True})))
    patch.object(GraphQLAPI, 'get_by_alias',
                 new=async_mock(return_value=('alias_uuid', 'alias_pull',
                                              {'alias': True})))

    asyncy_yaml = {
        'services': {
            'microservice/slack':
                {'image': 'microservice/slack', 'tag': 'v1'}
        },
        'expose': [
            {
                'service': 'naked_service'
            }
        ]
    }
    stories = {
        'services': ['microservice/slack', 'http', 'lastfm']
    }
    ret = await Apps.get_services(asyncy_yaml, logger, stories)
    assert ret == {
        'microservice/slack': {
            'tag': 'v1',
            'configuration': {
                'slug': True,
                'image': 'microservice/slack:v1',
                'uuid': 'slug_uuid',
            }
        },
        'lastfm': {
            'tag': 'latest',
            'configuration': {
                'alias': True,
                'image': 'alias_pull:latest',
                'uuid': 'alias_uuid',
            }
        },
        'http': {
            'configuration': {
                'alias': True,
                'image': 'alias_pull:latest',
                'uuid': 'alias_uuid'
            },
            'tag': 'latest',
        },
        'naked_service': {
            'configuration': {
                'alias': True,
                'image': 'alias_pull:latest',
                'uuid': 'alias_uuid'
            },
            'tag': 'latest',
        }
    }


@mark.parametrize('silent', [False, True])
@mark.parametrize('update_db', [False, True])
@mark.asyncio
async def test_destroy_app_exc(patch, async_mock, magic,
                               silent, update_db):
    app = magic()
    app.destroy = async_mock(side_effect=exc())
    patch.object(Database, 'update_release_state', new=async_mock())

    if silent:
        await Apps.destroy_app(app, silent, update_db_state=update_db)
    else:
        with pytest.raises(Exception):
            await Apps.destroy_app(app, silent, update_db_state=update_db)

    if update_db:
        assert Database.update_release_state.mock.mock_calls == [
            mock.call(app.logger, app.config, app.app_id, app.version,
                      ReleaseState.TERMINATING),
            mock.call(app.logger, app.config, app.app_id, app.version,
                      ReleaseState.TERMINATED)
        ]

    app.destroy.mock.assert_called()
