# -*- coding: utf-8 -*-
from frustum import Frustum

from logdna import LogDNAHandler


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
        ('lexicon-wait', 'debug', 'Processing line {} with "wait" method'),
        ('story-execution', 'debug', 'Received line "{}" from handler'),
        ('story-resolve', 'debug', 'Resolved "{}" to "{}"')
    ]

    def __init__(self, config):
        self.frustum = Frustum(config.logger_name, config.logger_level)
        self.logdna_key = config.logdna_key

    def logdna_handler(self, key, options):
        return LogDNAHandler(key, options)

    def start(self):
        for event in self.events:
            self.frustum.register_event(event[0], event[1], event[2])
        self.frustum.start_logger()

    def log(self, event, *args):
        self.frustum.log(event, *args)
