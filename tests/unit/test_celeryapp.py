# -*- coding: utf-8 -*-
from asyncy.CeleryApp import CeleryApp
from asyncy.Config import Config

from celery import Celery


def test_celeryapp(mocker):
    mocker.patch.object(Celery, '__init__', return_value=None)
    mocker.patch.object(Config, 'get', return_value='celery-broker')
    result = CeleryApp.start()
    Config.get.assert_called_with('broker')
    Celery.__init__.assert_called_with('asyncy', broker='celery-broker')
    assert isinstance(result, Celery)
