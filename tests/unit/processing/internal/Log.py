# -*- coding: utf-8 -*-
from pytest import fixture, mark

from storyruntime.processing.Services import Services
from storyruntime.processing.internal import Log


@fixture
def service_patch(patch):
    patch.object(Services, 'register_internal')


@mark.parametrize('level', ['info', 'error', 'warn', 'debug'])
@mark.asyncio
async def test_service_log_all(patch, service_patch, story, level):
    story.name = 'story_name'
    resolved_args = {
        'msg': 'Hello world!'
    }

    await getattr(Log, level)(story, None, resolved_args)
    getattr(story.app.logger, level)\
        .assert_called_with(f'{story.name}: Hello world!')
