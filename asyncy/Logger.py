# -*- coding: utf-8 -*-
from frustum import Frustum

from .Config import Config


class Logger:

    def __init__(self):
        self.frustum = Frustum(verbosity=Config.get('logger.verbosity'))

    def start(self):
        self.frustum.register_event('jwt-token', 'debug', 'Encoded token: {}')

    def log(self, event, *args):
        self.frustum.log(event, *args)
