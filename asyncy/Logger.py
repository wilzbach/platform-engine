# -*- coding: utf-8 -*-
from frustum import Frustum

from .Config import Config


class Logger:

    events = [
        ('jwt-token', 'debug', 'Encoded token: {}')
    ]

    def __init__(self):
        self.frustum = Frustum(verbosity=Config.get('logger.verbosity'))

    def register(self):
        for event in self.events:
            self.frustum.register_event(event[0], event[1], event[2])

    def log(self, event, *args):
        self.frustum.log(event, *args)
