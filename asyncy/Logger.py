# -*- coding: utf-8 -*-
from logging import LoggerAdapter, getLevelName

from frustum import Frustum

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import logging


cloud_logger = None

try:
    gcloud_logging_client = logging.Client()
    cloud_logger = gcloud_logging_client.logger('engine')
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

        if cloud_logger is not None:
            cloud_logger.log_struct(
                {
                    'app_id': app_id,
                    'version': version,
                    'message': message,
                    'level': getLevelName(level)
                }
            )

        message_pretty = f'{app_id}::{version} => {message}'
        self.logger.log(level, message_pretty, *args, **kwargs)


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
        getattr(self.frustum.logger, 'warn')(message)
