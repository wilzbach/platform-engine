# -*- coding: utf-8 -*-
import asyncio
import typing

from .ReportingAgent import ReportingAgent, ReportingEvent
from .agents.CleverTapAgent import CleverTapAgent
from .agents.SentryAgent import SentryAgent
from ..Config import Config
from ..Logger import Logger


class Reporter:
    _config = None
    _release = None
    _logger = None
    _exception_agents: typing.List[ReportingAgent] = []
    _event_agents: typing.List[ReportingAgent] = []

    @classmethod
    def init(cls, config: Config, glogger: Logger, release: str):
        cls._config = config
        cls._release = release
        cls._logger = glogger

        if config.REPORTING_SENTRY_DSN is not None:
            cls._exception_agents.append(SentryAgent(
                dsn=config.REPORTING_SENTRY_DSN,
                release=release, logger=cls._logger))

        if config.REPORTING_CLEVERTAP_ACCOUNT is not None and \
                config.REPORTING_CLEVERTAP_PASS is not None:
            cls._event_agents.append(CleverTapAgent(
                account_id=config.REPORTING_CLEVERTAP_ACCOUNT,
                account_pass=config.REPORTING_CLEVERTAP_PASS,
                release=release, logger=cls._logger
            ))

    @classmethod
    def capture_evt(cls, reporting_event: ReportingEvent = None):
        tasks = []
        if reporting_event.exc_info is not None:
            for agent in cls._exception_agents:
                tasks.append(cls._run_safely(agent, reporting_event))

        for agent in cls._event_agents:
            tasks.append(cls._run_safely(agent, reporting_event))

        for t in tasks:
            asyncio.get_event_loop().create_task(t)

    @classmethod
    async def _run_safely(cls, agent, reporting_event: ReportingEvent):
        try:
            await agent.capture(reporting_event)
        except Exception as e:
            cls._logger.error(
                f'Uncaught exception in {type(agent).__name__}: {str(e)}', e)
