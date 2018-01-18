# -*- coding: utf-8 -*-
from evenflow.Logger import Logger

from frustum import Frustum


def test_logger_init(mocker):
    mocker.patch.object(Frustum, '__init__', return_value=None)
    Logger()
    Frustum.__init__.assert_called_with(verbosity=1)
