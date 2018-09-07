# -*- coding: utf-8 -*-
import os
from json import load

from raven.contrib.tornado import AsyncSentryClient

from .Config import Config
from .Logger import Logger
from .processing import Story


class App:

    entrypoint = []
    sentry_client = None
    """
    This is the sentry_client for the engine, and not for reporting 
    errors of the app to the user (user's sentry account).
    For that, Storyscript stack traces must be generated and reported. 
    """

    def __init__(self, app_id: str, config: Config, logger: Logger,
                 stories: dict, services: dict, environment: dict,
                 sentry_client=None):
        self.app_id = app_id
        self.config = config
        self.logger = logger
        self.environment = environment
        self.stories = stories
        self.services = services
        self.sentry_client = sentry_client

    async def bootstrap(self):
        """
        Executes all stories found in stories.json.
        This enables the story to listen to pub/sub,
        register with the gateway, and queue cron jobs.
        """
        self.entrypoint = self.stories['entrypoint']
        self.stories = self.stories['stories']
        await self.run_stories()

    async def run_stories(self):
        """
        Executes all the stories.
        This enables the story to listen to pub/sub,
        register with the gateway, and queue cron jobs.
        """
        for story_name in self.entrypoint:
            try:
                await Story.run(self, self.logger, story_name)
            except Exception as e:
                self.logger.error('Failed to bootstrap story', exc=e)
                raise e

    async def destroy(self):
        """
        Destroys all stories, one at a time.
        """
        if self.entrypoint is None:
            return

        for story_name in self.entrypoint:
            try:
                await Story.destroy(self, self.logger, story_name)
            except Exception as e:
                self.logger.error('Failed to destroy story', exc=e)
                raise e
