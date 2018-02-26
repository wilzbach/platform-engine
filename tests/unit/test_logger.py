# -*- coding: utf-8 -*-
from asyncy.Logger import Logger

from frustum import Frustum

from pytest import fixture


@fixture
def logger(patch, config):
    patch.object(Frustum, '__init__', return_value=None)
    return Logger(config)


def test_logger_init(logger, config):
    verbosity = config.logger['verbosity']
    name = config.logger['name']
    Frustum.__init__.assert_called_with(name=name, verbosity=verbosity)


def test_logger_set_others(patch, logger):
    patch.object(Frustum, 'set_logger')
    logger.set_others()
    Frustum.set_logger.assert_called_with('amqp', 40)


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


def test_logger_start(patch, logger):
    patch.object(Logger, 'register')
    patch.object(Logger, 'set_others')
    logger.start()
    logger.register.assert_called_with()
    logger.set_others.assert_called_with()


def test_logger_log(patch, logger):
    patch.object(Frustum, 'log')
    logger.log('my-event')
    Frustum.log.assert_called_with('my-event')


def test_logger_log_args(patch, logger):
    patch.object(Frustum, 'log')
    logger.log('my-event', 'extra', 'args')
    Frustum.log.assert_called_with('my-event', 'extra', 'args')
