# -*- coding: utf-8 -*-
import json

import pytest
from pytest import fixture, mark

from storyruntime.Apps import Apps
from storyruntime.constants import ContextConstants
from storyruntime.entities.Multipart import FileFormField
from storyruntime.http_handlers.StoryEventHandler import \
    CLOUD_EVENTS_FILE_KEY, StoryEventHandler
from storyruntime.processing import Stories

import tornado
from tornado import ioloop


@fixture
def handler(logger, magic):
    return StoryEventHandler(magic(), magic(), logger=logger)


def test_get_ce_event_payload_json(handler: StoryEventHandler):
    handler.request.headers = {'Content-Type': 'application/json'}
    handler.request.body = '{"foo": "bar"}'
    assert handler.get_ce_event_payload() == {'foo': 'bar'}


def test_get_ce_event_payload_insensitive_headers(handler: StoryEventHandler):
    handler.request.headers = {'Content-Type': 'application/json'}
    json_body = {
        'eventType': 'http_request',
        'source': 'gateway',
        'data': {
            'headers': {
                'HelloWORLd-123': 'my_sensitive_value'
            }
        }
    }
    handler.request.body = json.dumps(json_body)
    parsed_payload = handler.get_ce_event_payload()
    parsed_payload['data']['headers']['helloworld-123'] = 'my_sensitive_value'
    parsed_payload['data']['headers']['HELLOWORLD-123'] = 'my_sensitive_value'


def test_get_ce_event_payload_invalid(handler: StoryEventHandler):
    handler.request.headers = {'Content-Type': 'foo/bar'}
    with pytest.raises(Exception):
        handler.get_ce_event_payload()


def test_get_ce_event_payload_multipart(handler: StoryEventHandler, magic):
    handler.request.headers = {'Content-Type': 'multipart/form-data'}
    ce_payload_file = magic()
    ce_payload_file.content_type = 'application/json'
    ce_payload_file.body = b'{"foo": "bar"}'

    handler.request.files = {
        CLOUD_EVENTS_FILE_KEY: [ce_payload_file]
    }

    assert handler.get_ce_event_payload() == {'foo': 'bar'}


@mark.asyncio
@mark.parametrize('throw_exc', [False, True])
async def test_post(patch, logger, magic, async_mock, throw_exc, handler):
    handler.request.body = '{}'
    hello_file = magic()
    hello_file.content_type = 'image/jpeg'
    hello_file.body = b'my_image'
    hello_file.filename = 'my_image_name'

    handler.request.files = {
        'hello': [hello_file],
        CLOUD_EVENTS_FILE_KEY: 'chill, ignored.'
    }
    handler.request.headers = {
        'Content-Type': 'application/json'
    }
    handler.logger = magic()
    patch.object(handler, 'get_argument',
                 side_effect=['hello.story', '1', 'app_id'])

    e = Exception()

    def exc(*args, **kwargs):
        raise e

    if throw_exc:
        patch.object(handler, 'run_story', new=async_mock(side_effect=exc))
        patch.object(handler, 'handle_story_exc')

    patch.object(Stories, 'run', new=async_mock())
    patch.object(Apps, 'get')
    patch.object(tornado, 'ioloop')
    patch.many(handler, ['finish'])

    hello_field = FileFormField(name='hello', body=hello_file.body,
                                filename=hello_file.filename,
                                content_type=hello_file.content_type)

    expected_context = {
        ContextConstants.service_event: {'data': {'hello': hello_field}},
        ContextConstants.server_io_loop: tornado.ioloop.IOLoop.current(),
        ContextConstants.server_request: handler
    }

    await handler.post()
    if throw_exc:
        handler.handle_story_exc.assert_called_with('app_id',
                                                    'hello.story', e)
    else:
        Stories.run.mock.assert_called_with(
            Apps.get('app_id'), Apps.get('app_id').logger,
            story_name='hello.story',
            context=expected_context, block='1')
