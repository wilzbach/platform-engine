# -*- coding: utf-8 -*-
from asyncy.processing.internal import Log
from asyncy.processing.internal.Services import Services

from pytest import fixture, mark


@fixture
def service_patch(patch):
    patch.object(Services, 'register')


@mark.parametrize('level', ['info', 'error', 'warn', 'debug'])
@mark.asyncio
async def test_service_log_all(patch, service_patch, story, level):
    story.name = 'story_name'
    resolved_args = {
        'msg': 'Hello world!'
    }

    await getattr(Log, level)(story, None, resolved_args)
    story.app.logger.log_raw.assert_called_with(level,
                                                f'{story.name}: Hello world!')
