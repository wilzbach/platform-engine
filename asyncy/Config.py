# -*- coding: utf-8 -*-
import os


class Config:

    defaults = {
        'gateway_url': 'gateway:8889',
        'logger_name': 'asyncy',
        'logger_level': 'debug',
        'DOCKER_HOST': 'http://localhost:2375',
        'DOCKER_TLS_VERIFY': '0',
        'DOCKER_CERT_PATH': '',
        'DOCKER_MACHINE_NAME': ''
    }

    engine_host = None
    engine_port = None

    def __init__(self):
        self.apply()

    def apply(self):
        """
        Applies values, taking them from the environment or from the defaults
        """
        for key, value in self.defaults.items():
            setattr(self, key, os.getenv(key, default=value)
                    .replace('tcp://', 'http://'))  # For CircleCI tests.

    def __getattribute__(self, name):
        """
        Gets an attribute or returns None
        """
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return None
