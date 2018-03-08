# -*- coding: utf-8 -*-
from asyncy.CeleryApp import CeleryApp
from asyncy.Config import Config

from celery import Celery


def test_celeryapp_start():
    result = CeleryApp.start(Config())
    assert isinstance(result, Celery)
