# -*- coding: utf-8 -*-
import json


from asyncy.Apps import Apps
from asyncy.constants import ContextConstants
from asyncy.http_handlers.StoryEventHandler import StoryEventHandler
from asyncy.processing import Story

from pytest import mark

import tornado
from tornado import ioloop


@mark.asyncio
@mark.parametrize('throw_exc', [False, True])
async def test_post(patch, logger, magic, async_mock, throw_exc):
    handler = StoryEventHandler(magic(), magic(), logger=logger)
    handler.request.body = '{}'
    handler.logger = magic()
    patch.object(handler, 'get_argument',
                 side_effect=['hello.story', '1', 'app_id'])

    e = Exception()

    def exc(*args, **kwargs):
        raise e

    if throw_exc:
        patch.object(handler, 'run_story', new=async_mock(side_effect=exc))
        patch.object(handler, 'handle_story_exc')

    patch.object(Story, 'run', new=async_mock())
    patch.object(Apps, 'get')
    patch.object(tornado, 'ioloop')
    patch.many(handler, ['finish'])

    expected_context = {
        ContextConstants.service_event: json.loads(handler.request.body),
        ContextConstants.server_io_loop: tornado.ioloop.IOLoop.current(),
        ContextConstants.server_request: handler
    }

    await handler.post()
    if throw_exc:
        handler.handle_story_exc.assert_called_with('hello.story', e)
    else:
        Story.run.mock.assert_called_with(
            Apps.get('app_id'), Apps.get('app_id').logger,
            story_name='hello.story',
            context=expected_context, block='1')
