# -*- coding: utf-8 -*-
from celery import Celery

from evenflow.CeleryApp import CeleryApp


def test_celeryapp():
    result = CeleryApp.start()
    assert isinstance(result, Celery)
    assert result.main == 'asyncy'
    assert result.conf.broker_url == 'amqp://user:password@localhost:5672/vhost'
