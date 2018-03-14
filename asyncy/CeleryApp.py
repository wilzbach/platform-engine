# -*- coding: utf-8 -*-
from celery import Celery


class CeleryApp:

    @staticmethod
    def start(config):
        print('version 141719')
        return Celery('asyncy', broker=config.broker)
