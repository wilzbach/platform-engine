# -*- coding: utf-8 -*-
import os


class Config:

    defaults = {
        'api_url': 'api-private:8080',
        'logger_name': 'asyncy',
        'logger_level': 'warning',
        'logdna_key': 'ingestion_key'
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
