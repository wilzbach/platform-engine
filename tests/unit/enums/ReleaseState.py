# -*- coding: utf-8 -*-
from storyruntime.enums.ReleaseState import ReleaseState


def test_locking():
    assert ReleaseState.QUEUED.value == 'QUEUED'
    assert ReleaseState.TERMINATING.value == 'TERMINATING'
    assert ReleaseState.TERMINATED.value == 'TERMINATED'
    assert ReleaseState.DEPLOYING.value == 'DEPLOYING'
    assert ReleaseState.DEPLOYED.value == 'DEPLOYED'
    assert ReleaseState.NO_DEPLOY.value == 'NO_DEPLOY'
    assert ReleaseState.FAILED.value == 'FAILED'
    assert ReleaseState.SKIPPED_CONCURRENT.value == 'SKIPPED_CONCURRENT'
