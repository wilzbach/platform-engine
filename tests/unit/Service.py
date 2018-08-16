# -*- coding: utf-8 -*-
import asyncio
from unittest.mock import MagicMock, Mock

from asyncy.App import App
from asyncy.Service import Service

from click.testing import CliRunner

from pytest import fixture, mark

import tornado


@fixture
def runner():
    return CliRunner()


def test_server(patch, runner):
    patch.many(App, ['bootstrap', 'destroy'])
    patch.many(tornado, ['web', 'ioloop'])
    patch.object(asyncio, 'get_event_loop')

    result = runner.invoke(Service.start)

    App.bootstrap.assert_called()

    tornado.ioloop.IOLoop.current.assert_called()
    tornado.ioloop.IOLoop.current.return_value.start.assert_called()

    assert result.exit_code == 0


def test_service_sig_handler(patch):
    patch.object(tornado, 'ioloop')
    Service.sig_handler(15)
    tornado.ioloop.IOLoop.instance()\
        .add_callback.assert_called_with(Service.shutdown)


def test_service_shutdown(patch):
    Service.server = MagicMock()
    patch.object(asyncio, 'get_event_loop')
    patch.object(Service, 'shutdown_app')
    Service.shutdown()
    asyncio.get_event_loop().create_task\
        .assert_called_with(Service.shutdown_app())


@mark.asyncio
async def test_service_shutdown_app(patch, async_mock):
    from asyncy import Service as ServiceWrapper
    ServiceWrapper.app.destroy = async_mock()

    patch.object(asyncio, 'get_event_loop')
    patch.object(tornado, 'ioloop')
    await Service.shutdown_app()

    ServiceWrapper.app.destroy.mock.assert_called_once()

    tornado.ioloop.IOLoop.instance() \
        .stop.assert_called_once()
    asyncio.get_event_loop().stop \
        .assert_called_once()
