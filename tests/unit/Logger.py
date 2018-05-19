# -*- coding: utf-8 -*-
from logging import LoggerAdapter

from asyncy.Logger import Adapter, Logger

from frustum import Frustum

from pytest import fixture


@fixture
def logger(patch, config):
    patch.init(Frustum)
    return Logger(config)


def test_adapter():
    assert issubclass(Adapter, LoggerAdapter)


def test_adapter_process():
    adapter = Adapter('logger', {'story': 'test.story', 'app': 'foobar'})
    result = adapter.process('message', {})
    assert result == ('foobar::test.story => message', {})


def test_adapter_process_reset():
    adapter = Adapter('logger', {'story': 'test.story', 'app': 'foobar'})
    result = adapter.process('1::old.story => message', {})
    assert result == ('foobar::test.story => message', {})


def test_logger_init(logger, config):
    name = config.logger_name
    level = config.logger_level
    Frustum.__init__.assert_called_with(name, level)


def test_logger_events_container_start(logger):
    message = 'Container {} is executing'
    assert logger.events[0] == ('container-start', 'info', message)


def test_logger_events_container_end(logger):
    message = 'Container {} has finished executing'
    assert logger.events[1] == ('container-end', 'info', message)


def test_logger_events_story_start(logger):
    message = 'Start processing story "{}" with id {}'
    assert logger.events[2] == ('story-start', 'info', message)


def test_logger_events_story_save(logger):
    message = 'Saved results of story "{}"'
    assert logger.events[3] == ('story-save', 'info', message)


def test_logger_events_story_end(logger):
    message = 'Finished processing story "{}" with id {}'
    assert logger.events[4] == ('story-end', 'info', message)


def test_logger_events_container_volume(logger):
    message = 'Created volume {}'
    assert logger.events[5] == ('container-volume', 'debug', message)


def test_logger_events_lexicon_if(logger):
    message = 'Processing line {} with "if" method against context {}'
    assert logger.events[6] == ('lexicon-if', 'debug', message)


def test_logger_events_lexicon_wait(logger):
    message = 'Processing line {} with "wait" method'
    assert logger.events[7] == ('lexicon-wait', 'debug', message)


def test_logger_events_story_execute(logger):
    message = 'Received line "{}" from handler'
    assert logger.events[8] == ('story-execution', 'debug', message)


def test_logger_events_story_resolve(logger):
    message = 'Resolved "{}" to "{}"'
    assert logger.events[9] == ('story-resolve', 'debug', message)


def test_logger_events_story_unless(logger):
    message = 'Processing line {} with "unless" method against context {}'
    assert logger.events[10] == ('lexicon-unless', 'debug', message)


def test_logger_events_service_init(logger):
    message = 'Starting Asyncy version {}'
    assert logger.events[11] == ('service-init', 'info', message)


def test_logger_events_http_init(logger):
    message = 'HTTP server bound to port {}'
    assert logger.events[13] == ('http-init', 'info', message)


def test_logger_events_http_run_story(logger):
    message = 'Received run request for story {} from app {} via HTTP'
    assert logger.events[14] == ('http-request-run-story', 'debug', message)


def test_logger_events_story_wait_err(logger):
    message = 'Cannot process line {} with "wait" method (unsupported)!'
    assert logger.events[14] == ('lexicon-wait-err', 'error', message)


def test_logger_adapter(patch, magic, logger):
    patch.init(Adapter)
    logger.frustum = magic()
    adapter = logger.adapter(1, 'name.story')
    assert isinstance(adapter, Adapter)
    extra = {'app': 1, 'story': 'name.story'}
    Adapter.__init__.assert_called_with(logger.frustum.logger, extra)


def test_logger_start(patch, logger):
    patch.many(Frustum, ['register_event', 'start_logger'])
    logger.events = [('event', 'level', 'message')]
    logger.start()
    Frustum.register_event.assert_called_with('event', 'level', 'message')
    Frustum.start_logger.assert_called_with()


def test_logger_adapt(patch, logger):
    patch.object(Logger, 'adapter')
    logger.adapt(1, 'name.story')
    Logger.adapter.assert_called_with(1, 'name.story')
    assert logger.frustum.logger == Logger.adapter()


def test_logger_log(patch, logger):
    patch.object(Frustum, 'log')
    logger.log('my-event')
    Frustum.log.assert_called_with('my-event')


def test_logger_log_raw(patch, logger):
    patch.object(logger, 'frustum')
    logger.log_raw('info', 'my-event')
    logger.frustum.logger.info.assert_called_with('my-event')


def test_logger_log_args(patch, logger):
    patch.object(Frustum, 'log')
    logger.log('my-event', 'extra', 'args')
    Frustum.log.assert_called_with('my-event', 'extra', 'args')
