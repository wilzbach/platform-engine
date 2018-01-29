# -*- coding: utf-8 -*-
from asyncy.CeleryTasks import app, logger

from celery import Celery


def test_celerytasks_app():
    assert isinstance(app, Celery)


def test_celerytasks_logger_start():
    assert len(logger.frustum.events) > 0
