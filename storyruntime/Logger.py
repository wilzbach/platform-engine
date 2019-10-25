# -*- coding: utf-8 -*-
import json
import os
import traceback
from distutils.util import strtobool
from logging import Formatter, LoggerAdapter, StreamHandler, getLevelName

from frustum import Frustum

from .Exceptions import StoryscriptError

log_json = strtobool(os.getenv("LOG_FORMAT_JSON", "False"))


class Adapter(LoggerAdapter):
    def log(self, level, message, *args, **kwargs):
        """
        Override the log method because the log level for the current
        message is not passed in process.
        """
        if not self.isEnabledFor(level):
            return

        exc = kwargs.get("exc_info")
        if exc and hasattr(exc, "message"):
            message = exc.message
        message = message.strip()
        message, kwargs = self.process(message, kwargs)

        app_id = self.extra["app_id"]
        version = self.extra["version"]

        if exc:
            if isinstance(exc, StoryscriptError):
                message = str(exc)
                del kwargs["exc_info"]
            else:
                tb = traceback.format_exc()
                message += "\n" + tb

        if log_json:
            json_log = {
                "app_id": app_id,
                "version": version,
                "level": getLevelName(level),
                "message": message,
            }

            self.logger.log(level, json_log, *args, **kwargs)
        else:
            message_pretty = f"{app_id}::{version} => {message}"
            self.logger.log(level, message_pretty, *args, **kwargs)


class JSONFormatter(Formatter):
    def format(self, record):
        return json.dumps(record.msg)


class Logger:
    events = [
        ("container-start", "info", "Container {} is executing"),
        ("container-end", "info", "Container {} has finished executing"),
        ("story-start", "info", 'Start processing story "{}"'),
        ("story-save", "info", 'Saved results of story "{}"'),
        ("story-end", "info", 'Finished processing story "{}"'),
        ("container-volume", "debug", "Created volume {}"),
        (
            "lexicon-if",
            "debug",
            'Processing line {} with "if" method against context {}',
        ),
        ("story-execution", "debug", 'Received line "{}" from handler'),
        (
            "lexicon-unless",
            "debug",
            'Processing line {} with "unless" method against context {}',
        ),
        (
            "service-init",
            "info",
            "Starting Storyscript Cloud Runtime version {}",
        ),
        ("http-init", "info", "HTTP server bound to port {}"),
        (
            "http-request-run-story",
            "debug",
            "Received run request for story {} via HTTP",
        ),
    ]

    def __init__(self, config):
        self.frustum = Frustum(config.LOGGER_NAME, config.LOGGER_LEVEL)

    def adapter(self, app_id, version):
        return Adapter(
            self.frustum.logger, {"app_id": app_id, "version": version}
        )

    def start(self):
        for event in self.events:
            self.frustum.register_event(event[0], event[1], event[2])
        self.frustum.start_logger()
        if log_json:
            self.set_json_formatter()

    def set_json_formatter(self):
        log_handler = StreamHandler()
        formatter = JSONFormatter()
        log_handler.setFormatter(formatter)
        self.frustum.logger.addHandler(log_handler)
        self.frustum.logger.propagate = False

    def adapt(self, app_id, version):
        self.frustum.logger = self.adapter(app_id, version)

    def log(self, event, *args):
        self.frustum.log(event, *args)

    def info(self, message):
        getattr(self.frustum.logger, "info")(message)

    def debug(self, message):
        getattr(self.frustum.logger, "debug")(message)

    def error(self, message, exc=None):
        getattr(self.frustum.logger, "error")(message, exc_info=exc)

    def warn(self, message):
        getattr(self.frustum.logger, "warning")(message)
