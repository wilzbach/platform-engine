# -*- coding: utf-8 -*-
from frustum import Frustum


class Logger:

    events = [
        ('github-autherr', 'error',
         'Github authentication for app {} and installation {} failed'),
        ('container-start', 'info', 'Container {} is running'),
        ('container-end', 'info', 'Container {} has finished'),
        ('story-start', 'info',
         'Start processing story "{}" for app {} with id {}'),
        ('story-save', 'info', 'Saved results of story "{}" for app {}'),
        ('story-end', 'info',
         'Finished processing story "{}" for app {} with id {}'),
        ('task-received', 'info', 'Received task for app {} with story "{}"'),
        ('container-volume', 'debug', 'Created volume {}'),
        ('jwt-token', 'debug', 'Encoded token: {}'),
        ('story-parse', 'debug', 'Parsed story {}'),
        ('story-resolve', 'debug', 'Resolved "{}" to "{}"'),
    ]

    def __init__(self, config):
        level = config.logger['level']
        name = config.logger['name']
        self.frustum = Frustum(name, level)

    def start(self):
        for event in self.events:
            self.frustum.register_event(event[0], event[1], event[2])
        self.frustum.start_logger()

    def log(self, event, *args):
        self.frustum.log(event, *args)
