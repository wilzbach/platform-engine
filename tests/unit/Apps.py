# -*- coding: utf-8 -*-
import asyncio
import select

import psycopg2
import pytest

from pytest import fixture, mark

from asyncy.Apps import Apps


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


def test_listen_to_releases(patch, db, magic, config, logger, exc):
    conn = db()

    patch.object(asyncio, 'run_coroutine_threadsafe', side_effect=exc)
    patch.object(select, 'select', return_value=[([], [], []), ([], [], []),
                                                 False])
    patch.object(Apps, 'reload_app')
    notif = magic()
    notif.payload = 'app_id'
    conn.notifies = [notif]
    loop = magic()

    with pytest.raises(Exception):
        Apps.listen_to_releases(config, logger, loop)

    conn.cursor().execute.assert_called_with('listen release;')
    Apps.reload_app.assert_called_with(config, logger, 'app_id')
    conn.set_isolation_level.assert_called_with(
        psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    asyncio.run_coroutine_threadsafe.assert_called_with(
        Apps.reload_app(), loop)


@mark.asyncio
async def test_destroy_all(patch, async_mock, magic):
    app = magic()
    app.destroy = async_mock()
    Apps.apps = {'app_id': app}
    app.app_id = 'app_id'
    await Apps.destroy_all()
    app.destroy.mock.assert_called()
    assert Apps.apps['app_id'] is None


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