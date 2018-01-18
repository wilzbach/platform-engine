# -*- coding: utf-8 -*-
from evenflow.Logger import Logger

from frustum import Frustum


def test_logger_init(mocker):
    mocker.patch.object(Frustum, '__init__', return_value=None)
    Logger()
    Frustum.__init__.assert_called_with(verbosity=1)


def test_logger_start(mocker):
    mocker.patch.object(Frustum, '__init__', return_value=None)
    mocker.patch.object(Frustum, 'register_event')
    logger = Logger()
    logger.start()
    message = 'Encoded token: {}'
    Frustum.register_event.assert_called_with('jwt-token', 'debug', message)
