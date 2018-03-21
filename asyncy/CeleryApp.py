# -*- coding: utf-8 -*-
from celery import Celery


class CeleryApp:

    @staticmethod
    def start(config):
        return Celery('asyncy', broker=config.broker)
