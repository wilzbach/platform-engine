# -*- coding: utf-8 -*-
from asyncy.CeleryApp import CeleryApp

from celery import Celery


def test_celeryapp(patch, config):
    patch.object(Celery, '__init__', return_value=None)
    result = CeleryApp.start(config)
    Celery.__init__.assert_called_with('asyncy', broker=config.broker)
    assert isinstance(result, Celery)
