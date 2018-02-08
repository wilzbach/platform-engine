# -*- coding: utf-8 -*-
from celery import Celery


class CeleryApp:

    def start(config):
        return Celery('asyncy', broker=config.broker)
