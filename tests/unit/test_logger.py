# -*- coding: utf-8 -*-
from asyncy.Logger import Logger

from frustum import Frustum

from pytest import fixture


@fixture
def logger(mocker, config):
    mocker.patch.object(Frustum, '__init__', return_value=None)
    return Logger()


def test_logger_init(logger, config):
    config.get.assert_called_with('logger.verbosity')
    Frustum.__init__.assert_called_with(verbosity=config.get())


def test_logger_events(logger):
    assert logger.events[0] == ('jwt-token', 'debug', 'Encoded token: {}')


def test_logger_register(mocker, logger):
    mocker.patch.object(Frustum, 'register_event')
    logger.events = [('event', 'level', 'message')]
    logger.register()
    Frustum.register_event.assert_called_with('event', 'level', 'message')


def test_logger_log(mocker, logger):
    mocker.patch.object(Frustum, 'log')
    logger.log('my-event')
    Frustum.log.assert_called_with('my-event')


def test_logger_log_args(mocker, logger):
    mocker.patch.object(Frustum, 'log')
    logger.log('my-event', 'extra', 'args')
    Frustum.log.assert_called_with('my-event', 'extra', 'args')
