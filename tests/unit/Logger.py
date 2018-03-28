# -*- coding: utf-8 -*-
from logging import LoggerAdapter

from asyncy.Logger import Adapter, Logger

from frustum import Frustum

from logdna import LogDNAHandler

from pytest import fixture


@fixture
def logger(patch, config):
    patch.init(Frustum)
    return Logger(config)


def test_adapter():
    assert issubclass(Adapter, LoggerAdapter)


def test_adapter_process():
    adapter = Adapter('logger', {'story': 'test.story', 'app': 1})
    result = adapter.process('message', {})
    assert result == ('1::test.story message', {})


def test_logger_init(logger, config):
    name = config.logger_name
    level = config.logger_level
    Frustum.__init__.assert_called_with(name, level)
    assert logger.logdna_key == config.logdna_key


def test_logger_events_container_start(logger):
    message = 'Container {} is running'
    assert logger.events[0] == ('container-start', 'info', message)


def test_logger_events_container_end(logger):
    message = 'Container {} has finished'
    assert logger.events[1] == ('container-end', 'info', message)


def test_logger_events_story_start(logger):
    message = 'Start processing story "{}" for app {} with id {}'
    assert logger.events[2] == ('story-start', 'info', message)


def test_logger_events_story_save(logger):
    message = 'Saved results of story "{}" for app {}'
    assert logger.events[3] == ('story-save', 'info', message)


def test_logger_events_story_end(logger):
    message = 'Finished processing story "{}" for app {} with id {}'
    assert logger.events[4] == ('story-end', 'info', message)


def test_logger_events_task_received(logger):
    message = 'Received task for app {} with story "{}"'
    assert logger.events[5] == ('task-received', 'info', message)


def test_logger_events_container_volume(logger):
    message = 'Created volume {}'
    assert logger.events[6] == ('container-volume', 'debug', message)


def test_logger_events_lexicon_if(logger):
    message = 'Processing line {} with "if" method against context {}'
    assert logger.events[7] == ('lexicon-if', 'debug', message)


def test_logger_events_lexicon_wait(logger):
    message = 'Processing line {} with "wait" method'
    assert logger.events[8] == ('lexicon-wait', 'debug', message)


def test_logger_events_story_execute(logger):
    message = 'Received line "{}" from handler'
    assert logger.events[9] == ('story-execution', 'debug', message)


def test_logger_events_story_resolve(logger):
    message = 'Resolved "{}" to "{}"'
    assert logger.events[10] == ('story-resolve', 'debug', message)


def test_logger_logdna_handler(patch, logger):
    patch.init(LogDNAHandler)
    result = logger.logdna_handler('key', {})
    LogDNAHandler.__init__.assert_called_with('key', {})
    assert isinstance(result, LogDNAHandler)


def test_logger_add_logdna(patch, magic, logger):
    patch.object(Logger, 'logdna_handler')
    logger.frustum = magic()
    logger.add_logdna()
    options = {'app': 'asyncy_engine'}
    Logger.logdna_handler.assert_called_with(logger.logdna_key, options)
    handler = Logger.logdna_handler()
    logger.frustum.logger.addHandler.assert_called_with(handler)


def test_logger_adapter(patch, magic, logger):
    patch.init(Adapter)
    logger.frustum = magic()
    adapter = logger.adapter(1, 'name.story')
    assert isinstance(adapter, Adapter)
    extra = {'app': 1, 'story': 'name.story'}
    Adapter.__init__.assert_called_with(logger.frustum.logger, extra)


def test_logger_start(patch, logger):
    patch.many(Frustum, ['register_event', 'start_logger'])
    patch.object(logger, 'add_logdna')
    logger.events = [('event', 'level', 'message')]
    logger.start()
    Frustum.register_event.assert_called_with('event', 'level', 'message')
    Frustum.start_logger.assert_called_with()
    assert logger.add_logdna.call_count == 1


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
