# -*- coding: utf-8 -*-
from logging import LoggerAdapter

from frustum import Frustum

from logdna import LogDNAHandler


class Adapter(LoggerAdapter):

    def process(self, message, kwargs):
        app = self.extra['app']
        story = self.extra['story']
        shards = message.split('=>')
        result = '{}::{} => {}'.format(app, story, shards[-1].strip())
        return result, kwargs


class Logger:

    events = [
        ('container-start', 'info', 'Container {} is running'),
        ('container-end', 'info', 'Container {} has finished'),
        ('story-start', 'info',
         'Start processing story "{}" for app {} with id {}'),
        ('story-save', 'info', 'Saved results of story "{}" for app {}'),
        ('story-end', 'info',
         'Finished processing story "{}" for app {} with id {}'),
        ('task-received', 'info', 'Received task for app {} with story "{}"'),
        ('container-volume', 'debug', 'Created volume {}'),
        ('lexicon-if', 'debug',
         'Processing line {} with "if" method against context {}'),
        ('lexicon-wait', 'debug', 'Processing line {} with "wait" method'),
        ('story-execution', 'debug', 'Received line "{}" from handler'),
        ('story-resolve', 'debug', 'Resolved "{}" to "{}"'),
        ('rpc-request-run-story', 'debug', 'Received run request for story {} from app {} via RPC'),
        ('service-init', 'info', 'Starting Asyncy version {}'),
        ('rpc-init', 'info', 'RPC server bound to port {}'),
        ('lexicon-unless', 'debug',
         'Processing line {} with "unless" method against context {}'),
    ]

    def __init__(self, config):
        self.frustum = Frustum(config.logger_name, config.logger_level)
        self.logdna_key = config.logdna_key

    def logdna_handler(self, key, options):
        return LogDNAHandler(key, options)

    def add_logdna(self):
        options = {'app': 'asyncy_engine'}
        handler = self.logdna_handler(self.logdna_key, options)
        self.frustum.logger.addHandler(handler)

    def adapter(self, app, story):
        return Adapter(self.frustum.logger, {'app': app, 'story': story})

    def start(self):
        for event in self.events:
            self.frustum.register_event(event[0], event[1], event[2])
        self.frustum.start_logger()
        self.add_logdna()

    def adapt(self, app, story):
        self.frustum.logger = self.adapter(app, story)

    def log(self, event, *args):
        self.frustum.log(event, *args)

    def log_raw(self, lvl, message):
        getattr(self.frustum.logger, lvl)(message)
