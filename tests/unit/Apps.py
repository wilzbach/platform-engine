# -*- coding: utf-8 -*-
import asyncio
import os
import select
import signal
from threading import Thread

from asyncy.App import App
from asyncy.Apps import Apps
from asyncy.GraphQLAPI import GraphQLAPI
from asyncy.Kubernetes import Kubernetes
from asyncy.Sentry import Sentry

import psycopg2

import pytest
from pytest import fixture, mark


@fixture
def exc():
    def foo(*args, **kwargs):
        raise Exception()

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
    app = magic()
    app.destroy = async_mock()
    Apps.apps = {'app_id': app}
    app.app_id = 'app_id'
    await Apps.destroy_all()
    app.destroy.mock.assert_called()
    assert Apps.apps['app_id'] is None


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
async def test_reload_app_no_story(patch, config, logger, db, async_mock):
    conn = db()
    app_id = 'app_id'
    app_dns = 'app_dns'

    patch.object(Apps, 'destroy_app', new=async_mock())
    patch.object(Apps, 'deploy_release', new=async_mock())

    release = ['app_id', 'version', 'env', None, 'maintenance', app_dns]
    conn.cursor().fetchone.return_value = release

    await Apps.reload_app(config, logger, app_id)

    Apps.deploy_release.mock.assert_not_called()


@mark.parametrize('raise_error', [True, False])
@mark.asyncio
async def test_reload_app(patch, config, logger, db, async_mock,
                          magic, exc, raise_error):
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

    release = ['app_id', 'version', 'env', 'stories', 'maintenance', app_dns]
    conn.cursor().fetchone.return_value = release

    await Apps.reload_app(config, logger, app_id)

    Apps.destroy_app.mock.assert_called_with(old_app, silent=True)
    Apps.deploy_release.mock.assert_called_with(
        config, logger, app_id, app_dns,
        release[1], release[2], release[3], release[4])

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


@mark.parametrize('raise_exc', [True, False])
@mark.parametrize('maintenance', [True, False])
@mark.asyncio
async def test_deploy_release(config, logger, magic, patch,
                              async_mock, raise_exc, exc, maintenance):
    patch.object(Sentry, 'capture_exc')
    patch.object(Kubernetes, 'clean_namespace', new=async_mock())
    Apps.apps = {}
    services = magic()
    patch.object(Apps, 'get_services', new=async_mock(return_value=services))
    patch.init(App)
    if raise_exc:
        patch.object(App, 'bootstrap', new=async_mock(side_effect=exc))
    else:
        patch.object(App, 'bootstrap', new=async_mock())

    await Apps.deploy_release(
        config, logger, 'app_id', 'app_dns', 'version', 'env',
        {'stories': True}, maintenance)

    if maintenance:
        logger.warn.assert_called()
    else:
        App.__init__.assert_called_with(
            'app_id', 'app_dns', 'version', config, logger,
            {'stories': True}, services, 'env')
        App.bootstrap.mock.assert_called()
        if raise_exc:
            assert Apps.apps.get('app_id') is None
            Sentry.capture_exc.assert_called()
        else:
            assert Apps.apps.get('app_id') is not None


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
@mark.asyncio
async def test_destroy_app_exc(patch, async_mock, magic, exc, silent):
    app = magic()
    app.destroy = async_mock(side_effect=exc)

    if silent:
        await Apps.destroy_app(app, silent)
    else:
        with pytest.raises(Exception):
            await Apps.destroy_app(app, silent)

    app.destroy.mock.assert_called()
