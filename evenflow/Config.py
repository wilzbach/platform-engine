# -*- coding: utf-8 -*-
import os


class Config():

    defaults = {
        'database': 'postgresql://postgres:postgres@localhost:5432/database',
        'broker': 'amqp://:@localhost:5672/',
        'github.pem_path': 'github.pem',
        'github.app_identifier': '123456789'
    }

    @classmethod
    def get(cls, option):
        if option in cls.defaults:
            return os.getenv(option, default=cls.defaults[option])
