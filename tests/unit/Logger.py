# -*- coding: utf-8 -*-
import json
import logging
from io import StringIO
from logging import LoggerAdapter

from frustum import Frustum

from pytest import fixture, mark

from storyruntime.Config import Config
from storyruntime.Logger import Adapter, JSONFormatter, Logger


@fixture
def logger(patch, config):
    patch.init(Frustum)
    return Logger(config)


def test_adapter():
    assert issubclass(Adapter, LoggerAdapter)


@mark.parametrize("enabled", [True, False])
def test_adapter_log(patch, magic, enabled):
    adapter = Adapter("logger", {"app_id": "foo", "version": "1.0"})

    cloud_logger = magic()

    adapter.logger = magic()
    patch.object(adapter, "isEnabledFor", return_value=enabled)
    patch.object(
        adapter, "process", return_value=("formatted_message", {"k": "v"})
    )
    adapter.log(logging.INFO, "this is my message", k="v")

    if not enabled:
        adapter.logger.log.assert_not_called()
        cloud_logger.worker._queue.put_nowait.assert_not_called()
        return

    adapter.process.assert_called_with("this is my message", {"k": "v"})
    adapter.logger.log.assert_called_with(
        logging.INFO, "foo::1.0 => formatted_message", k="v"
    )


def test_logger_init(logger, config):
    name = config.LOGGER_NAME
    level = config.LOGGER_LEVEL
    Frustum.__init__.assert_called_with(name, level)


def test_logger_events_container_start(logger):
    message = "Container {} is executing"
    assert logger.events[0] == ("container-start", "info", message)


def test_logger_events_container_end(logger):
    message = "Container {} has finished executing"
    assert logger.events[1] == ("container-end", "info", message)


def test_logger_events_story_start(logger):
    message = 'Start processing story "{}"'
    assert logger.events[2] == ("story-start", "info", message)


def test_logger_events_story_save(logger):
    message = 'Saved results of story "{}"'
    assert logger.events[3] == ("story-save", "info", message)


def test_logger_events_story_end(logger):
    message = 'Finished processing story "{}"'
    assert logger.events[4] == ("story-end", "info", message)


def test_logger_events_container_volume(logger):
    message = "Created volume {}"
    assert logger.events[5] == ("container-volume", "debug", message)


def test_logger_events_lexicon_if(logger):
    message = 'Processing line {} with "if" method against context {}'
    assert logger.events[6] == ("lexicon-if", "debug", message)


def test_logger_events_story_execute(logger):
    message = 'Received line "{}" from handler'
    assert logger.events[7] == ("story-execution", "debug", message)


def test_logger_events_story_unless(logger):
    message = 'Processing line {} with "unless" method against context {}'
    assert logger.events[8] == ("lexicon-unless", "debug", message)


def test_logger_events_service_init(logger):
    message = "Starting Storyscript Cloud Runtime version {}"
    assert logger.events[9] == ("service-init", "info", message)


def test_logger_events_http_init(logger):
    message = "HTTP server bound to port {}"
    assert logger.events[10] == ("http-init", "info", message)


def test_logger_events_http_run_story(logger):
    message = "Received run request for story {} via HTTP"
    assert logger.events[11] == ("http-request-run-story", "debug", message)


def test_logger_adapter(patch, magic, logger):
    patch.init(Adapter)
    logger.frustum = magic()
    adapter = logger.adapter("my_app", "1.0")
    assert isinstance(adapter, Adapter)
    extra = {"app_id": "my_app", "version": "1.0"}
    Adapter.__init__.assert_called_with(logger.frustum.logger, extra)


@mark.parametrize("log_json", [True, False])
def test_logger_start(patch, logger, log_json):
    patch.many(Frustum, ["register_event", "start_logger"])
    patch.object(logger, "set_json_formatter")
    import storyruntime.Logger as LoggerFile

    LoggerFile.log_json = log_json
    logger.events = [("event", "level", "message")]
    logger.start()
    Frustum.register_event.assert_called_with("event", "level", "message")
    Frustum.start_logger.assert_called_with()
    if log_json:
        logger.set_json_formatter.assert_called_with()
    else:
        logger.set_json_formatter.assert_not_called()


@mark.parametrize("with_exception", [True, False])
def test_logger_json_formatter(patch, with_exception):
    import storyruntime.Logger as LoggerFile

    LoggerFile.log_json = True
    config = Config()
    logger = Logger(config)
    logger.start()
    logger.adapt("app", "1.0")
    buffer = StringIO()
    log_handler = logging.StreamHandler(buffer)
    formatter = JSONFormatter()
    log_handler.setFormatter(formatter)
    logger.frustum.logger.logger.addHandler(log_handler)

    import traceback

    patch.object(traceback, "format_exc", return_value="exception_tb_content")
    expected_message = "my-event"
    expected_level = "INFO"
    if with_exception:
        expected_message = "my-event\nexception_tb_content"
        expected_level = "ERROR"
        try:
            raise Exception()
        except Exception as e:
            logger.error("my-event", e)
    else:
        logger.info("my-event")

    json_log = json.loads(buffer.getvalue())

    assert json_log == {
        "message": expected_message,
        "app_id": "app",
        "level": expected_level,
        "version": "1.0",
    }


def test_logger_set_json_formatter(magic, logger):
    logger.frustum = magic()
    logger.set_json_formatter()
    assert logger.frustum.logger.addHandler.call_count == 1
    assert logger.frustum.logger.propagate is False


def test_logger_adapt(patch, logger):
    patch.object(Logger, "adapter")
    logger.adapt(1, "name.story")
    Logger.adapter.assert_called_with(1, "name.story")
    assert logger.frustum.logger == Logger.adapter()


def test_logger_log(patch, logger):
    patch.object(Frustum, "log")
    logger.log("my-event")
    Frustum.log.assert_called_with("my-event")


def test_logger_log_args(patch, logger):
    patch.object(Frustum, "log")
    logger.log("my-event", "extra", "args")
    Frustum.log.assert_called_with("my-event", "extra", "args")


def test_logger_log_info(patch, logger):
    patch.object(logger, "frustum")
    logger.info("my-event")
    logger.frustum.logger.info.assert_called_with("my-event")


def test_logger_log_debug(patch, logger):
    patch.object(logger, "frustum")
    logger.debug("my-event")
    logger.frustum.logger.debug.assert_called_with("my-event")


def test_logger_log_warn(patch, logger):
    patch.object(logger, "frustum")
    logger.warn("my-event")
    logger.frustum.logger.warning.assert_called_with("my-event")


def test_logger_log_error(patch, logger):
    patch.object(logger, "frustum")
    logger.error("my-event")
    logger.frustum.logger.error.assert_called_with("my-event", exc_info=None)


def test_logger_log_error_with_exc(patch, logger):
    patch.object(logger, "frustum")
    logger.error("my-event", "exc")
    logger.frustum.logger.error.assert_called_with("my-event", exc_info="exc")
