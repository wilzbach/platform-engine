# -*- coding: utf-8 -*-
from logging import LoggerAdapter

from frustum import Frustum


class Adapter(LoggerAdapter):

    def process(self, message, kwargs):
        app = self.extra['app']
        story = self.extra['story']
        shards = message.split('=>')
        result = '{}::{} => {}'.format(app, story, shards[-1].strip())
        return result, kwargs


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
        ('lexicon-wait', 'debug', 'Processing line {} with "wait" method'),
        ('story-execution', 'debug', 'Received line "{}" from handler'),
        ('story-resolve', 'debug', 'Resolved "{}" to "{}"'),
        ('lexicon-unless', 'debug',
         'Processing line {} with "unless" method against context {}'),
        ('service-init', 'info', 'Starting Asyncy version {}'),
        ('rpc-init', 'info', 'RPC server bound to port {}'),
        ('rpc-request-run-story', 'debug',
         'Received run request for story {} via RPC'),
        ('lexicon-wait-err', 'error',
         'Cannot process line {} with "wait" method (unsupported)!'),
    ]

    def __init__(self, config):
        self.frustum = Frustum(config.logger_name, config.logger_level)

    def adapter(self, app, story):
        return Adapter(self.frustum.logger, {'app': app, 'story': story})

    def start(self):
        for event in self.events:
            self.frustum.register_event(event[0], event[1], event[2])
        self.frustum.start_logger()

    def adapt(self, app, story):
        self.frustum.logger = self.adapter(app, story)

    def log(self, event, *args):
        self.frustum.log(event, *args)

    def log_raw(self, lvl, message):
        getattr(self.frustum.logger, lvl)(message)
