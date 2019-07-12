# -*- coding: utf-8 -*-
import asyncio
import sys
from unittest.mock import MagicMock

from asyncy.Apps import Apps
from asyncy.Service import Service

from click.testing import CliRunner

import prometheus_client

import pytest
from pytest import fixture, mark

import tornado


@fixture
def runner():
    return CliRunner()


@mark.asyncio
async def test_server(patch, runner):
    patch.object(Service, 'init_wrapper')
    patch.object(prometheus_client, 'start_http_server')
    patch.many(tornado, ['web', 'ioloop', 'httpserver'])
    patch.object(asyncio, 'get_event_loop')

    result = runner.invoke(Service.start)

    Service.init_wrapper.assert_called()

    tornado.ioloop.IOLoop.current.assert_called()
    tornado.ioloop.IOLoop.current.return_value.start.assert_called()

    assert result.exit_code == 0


@mark.asyncio
async def test_init_wrapper(patch, async_mock):
    patch.object(Apps, 'init_all', new=async_mock())
    import asyncy.Service as ServiceFile
    ServiceFile.config = MagicMock()
    ServiceFile.logger = MagicMock()
    sentry = 'sentry_dsn'
    release = 'release_ver'
    await Service.init_wrapper(sentry, release)
    Apps.init_all.mock.assert_called_with(
        sentry, release, ServiceFile.config, ServiceFile.logger)


@mark.asyncio
async def test_init_wrapper_exc(patch, async_mock, magic):
    def exc(*args, **kwargs):
        raise Exception()

    patch.object(Apps, 'init_all', new=async_mock(side_effect=exc))
    patch.object(sys, 'exit')
    await Service.init_wrapper(magic(), magic())
    sys.exit.assert_called()


def test_service_sig_handler(patch):
    patch.object(tornado, 'ioloop')
    Service.sig_handler(15)
    tornado.ioloop.IOLoop.instance()\
        .add_callback.assert_called_with(Service.shutdown)


def test_service_shutdown(patch):
    import asyncy.Service as ServiceFile
    ServiceFile.server = MagicMock()
    patch.object(asyncio, 'get_event_loop')
    patch.object(Service, 'shutdown_app')
    Service.shutdown()
    asyncio.get_event_loop().create_task\
        .assert_called_with(Service.shutdown_app())


@mark.asyncio
async def test_service_shutdown_app(patch, async_mock):
    patch.object(asyncio, 'get_event_loop')
    patch.object(tornado, 'ioloop')
    patch.object(Apps, 'destroy_all', new=async_mock())
    await Service.shutdown_app()

    Apps.destroy_all.mock.assert_called_once()

    tornado.ioloop.IOLoop.instance() \
        .stop.assert_called_once()
    asyncio.get_event_loop().stop \
        .assert_called_once()
