# -*- coding: utf-8 -*-
from storyruntime.enums.AppEnvironment import AppEnvironment


def test_db_values():
    # The values below are production values.
    assert AppEnvironment.PRODUCTION.value == 'PRODUCTION'
    assert AppEnvironment.STAGING.value == 'STAGING'
    assert AppEnvironment.DEV.value == 'DEV'
