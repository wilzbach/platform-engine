# -*- coding: utf-8 -*-
import asyncio
import os
import select
import signal
from threading import Thread
from unittest import mock

from asyncy.App import App
from asyncy.Apps import Apps
from asyncy.Containers import Containers
from asyncy.Exceptions import AsyncyError
from asyncy.GraphQLAPI import GraphQLAPI
from asyncy.Kubernetes import Kubernetes
from asyncy.Logger import Logger
from asyncy.Sentry import Sentry
from asyncy.enums.ReleaseState import ReleaseState

import psycopg2

import pytest
from pytest import fixture, mark


@fixture
def exc():
    def foo(*args, **kwargs):
        raise Exception()

    return foo


@fixture
def asyncy_exc():
    def foo(*args, **kwargs):
        raise AsyncyError()

    return foo


@fixture
def db(patch, magic):
    def get():
        db = magic()
        patch.object(psycopg2, 'connect', return_value=db)
        return db

    return get


def test_listen_to_releases(patch, db, magic, config, logger):
    conn = db()

    def exc(*args, **kwargs):
        raise psycopg2.InterfaceError()

    patch.object(asyncio, 'run_coroutine_threadsafe', side_effect=exc)
    patch.object(select, 'select', side_effect=[([], [], []), ([], [], []),
                                                False])
    patch.object(Apps, 'reload_app')
    patch.many(os, ['kill', 'getpid'])
    notif = magic()
    notif.payload = 'app_id'
    conn.notifies = [notif]
    loop = magic()

    Apps.listen_to_releases(config, logger, loop)

    conn.cursor().execute.assert_called_with('listen release;')
    Apps.reload_app.assert_called_with(config, logger, 'app_id')
    conn.set_isolation_level.assert_called_with(
        psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    asyncio.run_coroutine_threadsafe.assert_called_with(
        Apps.reload_app(), loop)

    os.kill.assert_called_with(os.getpid.return_value, signal.SIGINT)


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
    patch.object(Sentry, 'capture_exc')

    err = BaseException()

    async def exc():
        raise err

    app.destroy = exc
    Apps.apps = {'app_id': app}
    app.app_id = 'app_id'
    await Apps.destroy_all()

    Sentry.capture_exc.assert_called_with(err)


@mark.asyncio
async def test_init_all(patch, magic, async_mock, config, logger, db):
    db()
    patch.object(Sentry, 'init')
    patch.init(Thread)
    patch.object(Thread, 'start')

    releases = [
        ['my_app_uuid']
    ]
    patch.object(Apps, 'get_all_app_uuids_for_deployment',
                 return_value=releases)
    patch.object(Apps, 'reload_app', new=async_mock())

    await Apps.init_all('sentry_dsn', 'release_ver', config, logger)
    Apps.reload_app.mock.assert_called_with(
        config, logger, 'my_app_uuid')

    Sentry.init.assert_called_with('sentry_dsn', 'release_ver')

    loop = asyncio.get_event_loop()
    Thread.__init__.assert_called_with(target=Apps.listen_to_releases,
                                       args=[config, logger, loop],
                                       daemon=True)
    Thread.start.assert_called()


def test_get(magic):
    app = magic()
    Apps.apps['app_id'] = app
    assert Apps.get('app_id') == app


@mark.asyncio
async def test_reload_app_ongoing_deployment(config, logger, patch):
    app_id = 'my_app'
    patch.object(Apps, 'new_pg_conn')

    await Apps.deployment_lock.try_acquire(app_id)

    await Apps.reload_app(config, logger, app_id)

    logger.warn.assert_called()
    Apps.new_pg_conn.assert_not_called()


@mark.asyncio
async def test_reload_app_no_story(patch, config, logger, db, async_mock):
    conn = db()
    app_id = 'app_id'
    app_dns = 'app_dns'

    patch.object(Apps, 'destroy_app', new=async_mock())
    patch.object(Apps, 'deploy_release', new=async_mock())

    release = ['app_id', 'version', 'env', None, 'maintenance', app_dns,
               'QUEUED']
    conn.cursor().fetchone.return_value = release

    await Apps.reload_app(config, logger, app_id)

    Apps.deploy_release.mock.assert_not_called()


@mark.parametrize('raise_error', [True, False])
@mark.parametrize('previous_state', ['QUEUED', 'FAILED'])
@mark.asyncio
async def test_reload_app(patch, config, logger, db, async_mock,
                          magic, exc, raise_error, previous_state):
    conn = db()
    old_app = magic()
    app_id = 'app_id'
    app_dns = 'app_dns'
    Apps.apps = {app_id: old_app}
    patch.object(Sentry, 'capture_exc')

    patch.object(Apps, 'destroy_app', new=async_mock())
    if raise_error:
        patch.object(Apps, 'deploy_release', new=async_mock(side_effect=exc))
    else:
        patch.object(Apps, 'deploy_release', new=async_mock())

    release = ['app_id', 'version', 'env', 'stories', 'maintenance', app_dns,
               previous_state, False]
    conn.cursor().fetchone.return_value = release

    await Apps.reload_app(config, logger, app_id)

    Apps.destroy_app.mock.assert_called_with(old_app, silent=True,
                                             update_db_state=True)
    if previous_state == 'FAILED':
        Apps.deploy_release.mock.assert_not_called()
        logger.warn.assert_called()
        logger.error.assert_not_called()
        return

    Apps.deploy_release.mock.assert_called_with(
        config, app_id, app_dns,
        release[1], release[2], release[3], release[4], release[7])

    if raise_error:
        logger.error.assert_called()
        Sentry.capture_exc.assert_called()
    else:
        logger.error.assert_not_called()


def test_get_all_app_uuids_for_deployment(patch, magic, config):
    conn = magic()
    patch.object(Apps, 'new_pg_conn', return_value=conn)
    query = 'select app_uuid from releases group by app_uuid;'
    ret = Apps.get_all_app_uuids_for_deployment(config)
    conn.cursor().execute.assert_called_with(query)
    assert ret == conn.cursor().fetchall()


@mark.parametrize('raise_exc', [None, exc, asyncy_exc])
@mark.parametrize('maintenance', [True, False])
@mark.parametrize('deleted', [True, False])
@mark.asyncio
async def test_deploy_release(config, magic, patch, deleted,
                              async_mock, raise_exc, maintenance):
    patch.object(Sentry, 'capture_exc')
    patch.object(Kubernetes, 'clean_namespace', new=async_mock())
    patch.object(Containers, 'init', new=async_mock())
    patch.many(Apps, ['update_release_state'])
    app_logger = magic()
    patch.object(Apps, 'make_logger_for_app', return_value=app_logger)
    Apps.apps = {}
    services = magic()
    patch.object(Apps, 'get_services', new=async_mock(return_value=services))
    patch.init(App)
    if raise_exc is not None:
        patch.object(App, 'bootstrap', new=async_mock(side_effect=raise_exc()))
    else:
        patch.object(App, 'bootstrap', new=async_mock())

    await Apps.deploy_release(
        config, 'app_id', 'app_dns', 'version', 'env',
        {'stories': True}, maintenance, deleted)

    if maintenance:
        assert Apps.update_release_state.call_count == 0
        app_logger.warn.assert_called()
    elif deleted:
        app_logger.warn.assert_called()
        Apps.update_release_state.assert_called_with(
            app_logger, config, 'app_id', 'version', ReleaseState.NO_DEPLOY)
    else:
        assert Apps.update_release_state.mock_calls[0] == mock.call(
            app_logger, config, 'app_id', 'version', ReleaseState.DEPLOYING)

        App.__init__.assert_called_with(
            'app_id', 'app_dns', 'version', config,
            app_logger,
            {'stories': True}, services, 'env')
        App.bootstrap.mock.assert_called()
        Containers.init.mock.assert_called()
        if raise_exc is not None:
            assert Apps.apps.get('app_id') is None
            if raise_exc == exc:
                Sentry.capture_exc.assert_called()
            assert Apps.update_release_state.mock_calls[1] == mock.call(
                app_logger, config, 'app_id', 'version', ReleaseState.FAILED)
        else:
            assert Apps.update_release_state.mock_calls[1] == mock.call(
                app_logger, config, 'app_id', 'version', ReleaseState.DEPLOYED)
            assert Apps.apps.get('app_id') is not None


def test_make_logger_for_app(patch, config):
    patch.many(Logger, ['start', 'adapt'])
    logger = Apps.make_logger_for_app(config, 'my_awesome_app', '17.1')
    logger.start.assert_called()
    logger.adapt.assert_called_with('my_awesome_app', '17.1')


@mark.asyncio
async def test_update_release_state(patch, logger, config):
    patch.object(Apps, 'new_pg_conn')
    expected_query = 'update releases ' \
                     'set state = %s ' \
                     'where app_uuid = %s and id = %s;'

    Apps.update_release_state(logger, config, 'app_id', 'version',
                              ReleaseState.DEPLOYED)

    Apps.new_pg_conn.assert_called_with(config)
    Apps.new_pg_conn.return_value.cursor.assert_called()
    Apps.new_pg_conn.return_value.cursor \
        .return_value.execute.assert_called_with(
            expected_query, (ReleaseState.DEPLOYED.value, 'app_id', 'version'))

    Apps.new_pg_conn.return_value.commit.assert_called()
    Apps.new_pg_conn.return_value.cursor.return_value.close.assert_called()
    Apps.new_pg_conn.return_value.close.assert_called()


@mark.asyncio
async def test_get_services(patch, logger, async_mock):
    patch.object(GraphQLAPI, 'get_by_slug',
                 new=async_mock(return_value=('slug_pull', {'slug': True})))
    patch.object(GraphQLAPI, 'get_by_alias',
                 new=async_mock(return_value=('alias_pull', {'alias': True})))

    asyncy_yaml = {
        'services': {
            'microservice/slack':
                {'image': 'microservice/slack', 'tag': 'v1'}
        }
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
                'image': 'microservice/slack:v1'
            }
        },
        'lastfm': {
            'tag': 'latest',
            'configuration': {
                'alias': True,
                'image': 'alias_pull:latest'
            }
        },
        'http': {
            'configuration': {
                'alias': True,
                'image': 'alias_pull:latest'
            },
            'tag': 'latest'
        }
    }


@mark.parametrize('silent', [False, True])
@mark.parametrize('update_db', [False, True])
@mark.asyncio
async def test_destroy_app_exc(patch, async_mock, magic, exc,
                               silent, update_db):
    app = magic()
    app.destroy = async_mock(side_effect=exc)
    patch.object(Apps, 'update_release_state')

    if silent:
        await Apps.destroy_app(app, silent, update_db_state=update_db)
    else:
        with pytest.raises(Exception):
            await Apps.destroy_app(app, silent, update_db_state=update_db)

    if update_db:
        assert Apps.update_release_state.mock_calls == [
            mock.call(app.logger, app.config, app.app_id, app.version,
                      ReleaseState.TERMINATING),
            mock.call(app.logger, app.config, app.app_id, app.version,
                      ReleaseState.TERMINATED)
        ]

    app.destroy.mock.assert_called()
