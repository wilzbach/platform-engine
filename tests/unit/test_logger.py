# -*- coding: utf-8 -*-
from asyncy.Config import Config
from asyncy.Logger import Logger

from frustum import Frustum


from pytest import fixture


@fixture
def config(mocker):
    mocker.patch.object(Config, 'get')
    return Config


@fixture
def logger(mocker, config):
    mocker.patch.object(Frustum, '__init__', return_value=None)
    return Logger()


def test_logger_init(logger):
    Config.get.assert_called_with('logger.verbosity')
    Frustum.__init__.assert_called_with(verbosity=Config.get())


def test_logger_start(mocker, logger):
    mocker.patch.object(Frustum, 'register_event')
    logger.start()
    message = 'Encoded token: {}'
    Frustum.register_event.assert_called_with('jwt-token', 'debug', message)


def test_logger_log(mocker, logger):
    mocker.patch.object(Frustum, 'log')
    logger.log('my-event')
    Frustum.log.assert_called_with('my-event')


def test_logger_log_args(mocker, logger):
    mocker.patch.object(Frustum, 'log')
    logger.log('my-event', 'extra', 'args')
    Frustum.log.assert_called_with('my-event', 'extra', 'args')
