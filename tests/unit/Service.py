# -*- coding: utf-8 -*-
from asyncy.App import App
from asyncy.Service import Service

from click.testing import CliRunner

from pytest import fixture

import tornado


@fixture
def runner():
    return CliRunner()


@fixture
def kwargs():
    return {'block': None, 'context': None, 'environment': None, 'start': None}


def sleep():
    raise OSError


def test_server(patch, runner):
    patch.object(App, 'bootstrap')
    patch.many(tornado, ['web', 'ioloop'])

    result = runner.invoke(Service.start)

    App.bootstrap.assert_called_with()

    tornado.ioloop.IOLoop.current.assert_called()
    tornado.ioloop.IOLoop.current.return_value.start.assert_called()
    assert result.exit_code == 0
