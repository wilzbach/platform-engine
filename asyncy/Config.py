# -*- coding: utf-8 -*-
import os


class Config():

    defaults = {
        'database': 'postgresql://postgres:postgres@localhost:5432/asyncy',
        'mongo': 'mongodb://localhost:27017/',
        'broker': 'amqp://:@localhost:5672/',
        'logger.verbosity': 1,
        'github.app_name': 'myapp',
        'github.pem_path': 'github.pem',
        'github.app_identifier': '123456789'
    }

    @classmethod
    def get(cls, option):
        if option in cls.defaults:
            return os.getenv(option, default=cls.defaults[option])
