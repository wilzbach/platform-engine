# -*- coding: utf-8 -*-
from frustum import Frustum
from celery.utils.log import get_task_logger


class Logger:

    events = [
        ('container-run', 'debug', 'Container {} run'),
        ('jwt-token', 'debug', 'Encoded token: {}'),
        ('story-parse', 'debug', 'Parsed story {}'),
        ('story-resolve', 'debug', 'Resolved {} to {}'),
        ('task-end', 'debug', 'Previous task ended'),
        ('task-received', 'debug', 'Received task for app {} with story {}'),
        ('task-start', 'debug', 'Start task for app {} with story {} id: {}'),
    ]

    def __init__(self, config):
        verbosity = config.logger['verbosity']
        name = config.logger['name']
        self.frustum = Frustum(name=name, verbosity=verbosity)

    def set_others(self):
        """
        Sets third party loggers to an appropriate value
        """
        self.frustum.set_logger('amqp', 40)

    def register(self):
        for event in self.events:
            self.frustum.register_event(event[0], event[1], event[2])

    def start(self):
        self.register()
        self.set_others()

    def log(self, event, *args):
        self.frustum.log(event, *args)
