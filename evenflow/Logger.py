# -*- coding: utf-8 -*-c
from frustum import Frustum


class Logger:

    def __init__(self, verbosity=1):
        self.frustum = Frustum(verbosity=1)

    def start(self):
        self.frustum.register_event('jwt-token', 'debug', 'Encoded token: {}')

    def log(self, event, *args):
        self.frustum.log(event, *args)
