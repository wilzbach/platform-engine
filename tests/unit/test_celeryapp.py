# -*- coding: utf-8 -*-
from celery import Celery

from evenflow.CeleryApp import CeleryApp


def test_celeryapp(mocker):
    mocker.patch.object(Celery, '__init__', return_value=None)
    result = CeleryApp.start()
    broker = 'amqp://user:password@localhost:5672/vhost'
    Celery.__init__.assert_called_with('asyncy', broker=broker)
    assert isinstance(result, Celery)
