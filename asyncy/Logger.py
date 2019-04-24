# -*- coding: utf-8 -*-
import json
import os
from distutils.util import strtobool
from logging import Formatter, LoggerAdapter, StreamHandler, getLevelName

from frustum import Frustum

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import logging
from google.cloud.logging.handlers.transports.background_thread \
    import BackgroundThreadTransport
from google.cloud.logging.resource import Resource

cloud_logger_bg = None

try:
    gcloud_logging_client = logging.Client()
    cloud_logger_bg = BackgroundThreadTransport(
        gcloud_logging_client, 'engine')
except DefaultCredentialsError:
    print('Cloud logging disabled')


class Adapter(LoggerAdapter):

    def log(self, level, message, *args, **kwargs):
        """
        Override the log method because the log level for the current
        message is not passed in process.
        """
        if not self.isEnabledFor(level):
            return

        message = message.strip()
        message, kwargs = self.process(message, kwargs)

        app_id = self.extra['app_id']
        version = self.extra['version']

        if cloud_logger_bg is not None:
            # The following usage is highly unconventional:
            # There appears to be no way to log a structured log message
            # asynchronously using the cloud logging client properly.
            # However, internally, the library uses structured logging. As long
            # as we queue the right payload into the worker's queue, we're OK.
            # This works well with google-cloud-logging==1.9.0.
            # It looks shady, but the only decent way to use the async logging
            # support for Stackdriver.
            cloud_logger_bg.worker._queue.put_nowait(
                {
                    'info': {
                        'app_id': app_id,
                        'version': version,
                        'message': message,
                        'level': getLevelName(level)
                    },
                    'severity': getLevelName(level),
                    'resource': Resource(type='global', labels={})
                }
            )

        message_pretty = f'{app_id}::{version} => {message}'
        self.logger.log(level, message_pretty, *args, **kwargs)


class JSONFormatter(Formatter):

    def format(self, record):
        return json.dumps({
            'message': record.msg,
            'app_id': record.app_id,
            'version': record.version
        })


class Logger:
    events = [
        ('container-start', 'info', 'Container {} is executing'),
        ('container-end', 'info', 'Container {} has finished executing'),
        ('story-start', 'info',
         'Start processing story "{}" with id {}'),
        ('story-save', 'info', 'Saved results of story "{}"'),
        ('story-end', 'info',
         'Finished processing story "{}" with id {}'),
        ('container-volume', 'debug', 'Created volume {}'),
        ('lexicon-if', 'debug',
         'Processing line {} with "if" method against context {}'),
        ('story-execution', 'debug', 'Received line "{}" from handler'),
        ('story-resolve', 'debug', 'Resolved "{}" to "{}"'),
        ('lexicon-unless', 'debug',
         'Processing line {} with "unless" method against context {}'),
        ('service-init', 'info', 'Starting Asyncy version {}'),
        ('http-init', 'info', 'HTTP server bound to port {}'),
        ('http-request-run-story', 'debug',
         'Received run request for story {} via HTTP'),
    ]

    def __init__(self, config):
        self.frustum = Frustum(config.LOGGER_NAME, config.LOGGER_LEVEL)

    def adapter(self, app_id, version):
        return Adapter(self.frustum.logger,
                       {'app_id': app_id, 'version': version})

    def start(self):
        for event in self.events:
            self.frustum.register_event(event[0], event[1], event[2])
        self.frustum.start_logger()
        log_json = strtobool(os.getenv('LOG_FORMAT_JSON', 'False'))
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
        getattr(self.frustum.logger, 'info')(message)

    def debug(self, message):
        getattr(self.frustum.logger, 'debug')(message)

    def error(self, message, exc=None):
        getattr(self.frustum.logger, 'error')(message, exc_info=exc)

    def warn(self, message):
        getattr(self.frustum.logger, 'warning')(message)
