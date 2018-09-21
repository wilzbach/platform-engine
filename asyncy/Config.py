# -*- coding: utf-8 -*-
import os
import socket


class Config:

    defaults = {
        'ASYNCY_HTTP_GW_HOST': 'gateway',
        'LOGGER_NAME': 'asyncy',
        'LOGGER_LEVEL': 'debug',
        'DOCKER_HOST': 'http://localhost:2375',
        'DOCKER_TLS_VERIFY': '0',
        'DOCKER_CERT_PATH': '',
        'DOCKER_MACHINE_NAME': '',
        'POSTGRES': 'options='
                    '--search_path=app_public,app_hidden,app_private,public '
                    'dbname=postgres user=postgres',
        'ENGINE_HOST': socket.gethostname()
    }

    ENGINE_PORT = None

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
