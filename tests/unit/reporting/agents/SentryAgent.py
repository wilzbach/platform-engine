from pytest import mark

import sentry_sdk
from sentry_sdk import Scope

from storyruntime.Exceptions import StoryscriptError
from storyruntime.entities.ReportingEvent import ReportingEvent
from storyruntime.reporting.agents.SentryAgent import SentryAgent


def test_create_agent(patch, magic):
    logger = magic()
    patch.object(sentry_sdk, 'init')

    sentry_agent = SentryAgent(
        dsn='sentry_dsn',
        release='release',
        logger=logger
    )

    sentry_sdk.init.assert_called_with(
        dsn='sentry_dsn',
        release='release',
        max_breadcrumbs=0,
        integrations=[],
        default_integrations=False
    )

    assert sentry_agent._logger == logger
    assert sentry_agent._release == 'release'


@mark.parametrize('ex', [Exception(), StoryscriptError()])
@mark.asyncio
async def test_capture(patch, magic, async_mock, ex):
    logger = magic()

    patch.object(sentry_sdk, 'init')
    patch.object(sentry_sdk, 'capture_exception')
    patch.object(Scope, 'clear')
    patch.object(Scope, '__setattr__')

    sentry_agent = SentryAgent(
        dsn='sentry_dsn',
        release='release',
        logger=logger
    )

    expected_story_line = '28'
    expected_story_name = 'story_name'

    await sentry_agent.capture(
        re=ReportingEvent(
            exc_info=ex,
            app_uuid='app_uuid',
            app_name='app_name',
            app_version='app_version',
            story_line='28',
            story_name='story_name',
            owner_email='foo@foo.com'
        )
    )

    if isinstance(ex, StoryscriptError):
        sentry_sdk.capture_exception.assert_not_called()
        return

    Scope.__setattr__.assert_called_with(
        'user', {
            'platform_release': 'release',
            'app_uuid': 'app_uuid',
            'app_name': 'app_name',
            'app_version': 'app_version',
            'story_name': expected_story_name,
            'story_line': expected_story_line,
            'email': 'foo@foo.com'
        })

    sentry_sdk.capture_exception.assert_called_with(error=ex)
    assert Scope.clear.call_count == 2
