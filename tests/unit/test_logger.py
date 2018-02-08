# -*- coding: utf-8 -*-
from asyncy.Logger import Logger

from frustum import Frustum

from pytest import fixture


@fixture
def logger(patch, config):
    patch.object(Frustum, '__init__', return_value=None)
    return Logger(config)


def test_logger_init(logger, config):
    Frustum.__init__.assert_called_with(verbosity=config.logger['verbosity'])


def test_logger_events(logger):
    assert logger.events[0] == ('container-run', 'debug', 'Container {} run')
    assert logger.events[1] == ('jwt-token', 'debug', 'Encoded token: {}')
    assert logger.events[2] == ('story-parse', 'debug', 'Parsed story {}')
    assert logger.events[3] == ('story-resolve', 'debug', 'Resolved {} to {}')
    assert logger.events[4] == ('task-end', 'debug', 'Previous task ended')
    message = 'Start task for app {} with story {} id: {}'
    assert logger.events[5] == ('task-start', 'debug', message)


def test_logger_register(patch, logger):
    patch.object(Frustum, 'register_event')
    logger.events = [('event', 'level', 'message')]
    logger.register()
    Frustum.register_event.assert_called_with('event', 'level', 'message')


def test_logger_log(patch, logger):
    patch.object(Frustum, 'log')
    logger.log('my-event')
    Frustum.log.assert_called_with('my-event')


def test_logger_log_args(patch, logger):
    patch.object(Frustum, 'log')
    logger.log('my-event', 'extra', 'args')
    Frustum.log.assert_called_with('my-event', 'extra', 'args')
