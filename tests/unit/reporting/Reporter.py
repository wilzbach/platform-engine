# -*- coding: utf-8 -*-
import asyncio
from unittest import mock

from pytest import fixture, mark

from storyruntime.Config import Config
from storyruntime.reporting.Reporter import Reporter
from storyruntime.reporting.agents.CleverTapAgent import CleverTapAgent
from storyruntime.reporting.agents.SentryAgent import SentryAgent


@fixture
def config():
    config = Config()
    config.REPORTING_SENTRY_DSN = 'sentry_dsn'
    config.REPORTING_CLEVERTAP_ACCOUNT = 'account'
    config.REPORTING_CLEVERTAP_PASS = 'pass'

    return config


def test_init(patch, config, logger):
    patch.init(SentryAgent)
    patch.init(CleverTapAgent)

    Reporter.init(config, logger, 'release')

    logger = Reporter._logger

    SentryAgent.__init__.assert_called_with(
        dsn='sentry_dsn',
        release='release',
        logger=logger
    )

    CleverTapAgent.__init__.assert_called_with(
        account_id='account',
        account_pass='pass',
        release='release',
        logger=logger
    )


@mark.parametrize('with_exc', [True, False])
def test_capture_evt(patch, magic, with_exc):
    exception_agent = magic()
    event_agent = magic()
    Reporter._exception_agents = [exception_agent]
    Reporter._event_agents = [event_agent]

    patch.object(Reporter, '_run_safely')

    patch.object(asyncio, 'get_event_loop')

    asyncio.get_event_loop.return_value = magic()

    re = magic()

    if with_exc:
        re.exc_info = Exception()
    else:
        re.exc_info = None

    Reporter.capture_evt(re)

    if with_exc:
        assert asyncio.get_event_loop().create_task.call_count == 2

        assert Reporter._run_safely.mock_calls == [
            mock.call(exception_agent, re),
            mock.call(event_agent, re)
        ]
    else:
        assert asyncio.get_event_loop().create_task.call_count == 1

        assert Reporter._run_safely.mock_calls == [
            mock.call(event_agent, re)
        ]


@mark.asyncio
async def test_run_safely(magic, patch, async_mock):
    agent = magic()
    re = magic()

    patch.object(agent, 'capture', new=async_mock())

    await Reporter._run_safely(agent, re)

    agent.capture.mock.assert_called_with(re)


@mark.asyncio
async def test_run_safely_exc(magic, patch, async_mock):
    agent = magic()
    re = magic()
    Reporter._logger = magic()
    patch.object(Reporter._logger, 'error')

    patch.object(agent, 'capture', new=async_mock(side_effect=Exception()))

    await Reporter._run_safely(agent, re)

    Reporter._logger.error.assert_called()
