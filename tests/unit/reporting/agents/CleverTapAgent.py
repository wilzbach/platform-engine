import json
import time

from pytest import mark

from storyruntime.entities.ReportingEvent import ReportingEvent
from storyruntime.reporting.agents.CleverTapAgent import CleverTapAgent
from storyruntime.utils.HttpUtils import HttpUtils

from tornado.httpclient import AsyncHTTPClient


def test_should_throttle(magic):
    agent = CleverTapAgent(magic(), magic(), magic(), magic())
    re = magic()
    re.app_uuid = 'app_uuid'
    re.event_name = 'event_name'

    assert agent.should_throttle(re) is False
    assert agent.should_throttle(re) is True
    assert agent.should_throttle(re) is True


@mark.asyncio
async def test_capture_no_event_name(patch, magic, async_mock):
    re = magic()
    re.event_name = None

    patch.init(AsyncHTTPClient)
    patch.object(HttpUtils, 'fetch_with_retry', new=async_mock())

    agent = CleverTapAgent(magic(), magic(), magic(), magic())

    await agent.capture(re)

    HttpUtils.fetch_with_retry.mock.assert_not_called()


@mark.parametrize('throttled', [True, False])
@mark.asyncio
async def test_capture(patch, magic, async_mock, throttled):
    logger = magic()

    _time = int(time.time())
    patch.object(time, 'time', return_value=_time)

    patch.init(AsyncHTTPClient)
    patch.object(HttpUtils, 'fetch_with_retry', new=async_mock())
    patch.object(CleverTapAgent, 'should_throttle', return_value=throttled)

    clevertap_agent = CleverTapAgent(
        account_id='account_id',
        account_pass='account_pass',
        release='release',
        logger=logger
    )

    AsyncHTTPClient.__init__.assert_called()

    re = ReportingEvent(exc_info=BaseException(), app_uuid='app_uuid',
                        app_name='app_name', app_version='app_version',
                        story_line='28', story_name='story_name',
                        owner_email='foo@foo.com', event_name='event_name',
                        owner_uuid='owner_uuid_123')
    await clevertap_agent.capture(re=re)

    CleverTapAgent.should_throttle.assert_called_with(re)

    if throttled:
        HttpUtils.fetch_with_retry.mock.assert_not_called()
        return

    HttpUtils.fetch_with_retry.mock.assert_called_with(
        tries=3, logger=logger,
        url='https://api.clevertap.com/1/upload',
        http_client=clevertap_agent._http_client,
        kwargs={
            'method': 'POST',
            'body': json.dumps({'d': [{
                'ts': _time,
                'identity': 'owner_uuid_123',
                'evtName': 'event_name',
                'evtData': {
                    'Platform release': 'release',
                    'App name': 'app_name',
                    'Version': 'app_version',
                    'Story name': 'story_name',
                    'Story line': '28'
                },
                'type': 'event'
            }]}),
            'headers': {
                'X-CleverTap-Account-Id': 'account_id',
                'X-CleverTap-Passcode': 'account_pass',
                'Content-Type': 'application/json; charset=utf-8'
            }
        })
