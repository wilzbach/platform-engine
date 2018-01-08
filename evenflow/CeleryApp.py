# -*- coding: utf-8 -*-
from celery import Celery

from .Config import Config


class CeleryApp:

    def start():
        broker = Config.get('broker')
        return Celery('asyncy', broker=broker)
