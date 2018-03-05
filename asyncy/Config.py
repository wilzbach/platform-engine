# -*- coding: utf-8 -*-
import os


class Config:

    defaults = {
        'database': 'postgresql://postgres:postgres@localhost:5432/asyncy',
        'mongo': 'mongodb://localhost:27017/',
        'broker': 'amqp://:@localhost:5672/',
        'logger_name': 'asyncy',
        'logger_level': 'warning',
        'github_app_name': 'myapp',
        'github_pem_path': 'github.pem',
        'github_app_identifier': '123456789'
    }

    def __init__(self):
        self.apply()

    def apply(self):
        """
        Applies values, taking them from the environment or from the defaults
        """
        for key, value in self.defaults.items():
            setattr(self, key, os.getenv(key, default=value))

    def __getattribute__(self, name):
        """
        Gets an attribute or returns None
        """
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return None
