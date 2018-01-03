# -*- coding: utf-8 -*-
from celery import Celery


class CeleryApp:

    def start():
        broker = 'amqp://user:password@localhost:5672/vhost'
        return Celery('asyncy', broker=broker)
