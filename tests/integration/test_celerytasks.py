# -*- coding: utf-8 -*-
from celery import Celery

from evenflow.CeleryTasks import app, logger


def test_celerytasks_app():
    assert isinstance(app, Celery)


def test_celerytasks_logger_start():
    assert len(logger.frustum.events) > 0
