# -*- coding: utf-8 -*-
from evenflow.CeleryTasks import logger


def test_celerytasks_logger_start():
    assert len(logger.frustum.events) > 0
