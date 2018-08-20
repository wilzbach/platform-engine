# -*- coding: utf-8 -*-
import os
from json import load

from raven.contrib.tornado import AsyncSentryClient

from .processing import Story


class App:

    environment = {}
    entrypoint = []
    stories = {}
    services = {}
    sentry_client = None

    def __init__(self, config, logger, beta_user_id=None,
                 sentry_dsn=None, release=None):
        self.config = config
        self.beta_user_id = beta_user_id
        self.logger = logger

        self.sentry_client = AsyncSentryClient(
            dsn=sentry_dsn,
            release=release
        )

    @staticmethod
    def load_file(filepath):
        datapath = os.getenv('ASSET_DIR', os.getcwd())
        path = os.path.join(datapath, filepath)
        if os.path.exists(path):
            with open(path, 'r') as file:
                return load(file)

    async def bootstrap(self):
        """
        Executes all stories found in stories.json.
        This enables the story to listen to pub/sub,
        register with the gateway, and queue cron jobs.
        """
        self.environment = self.load_file('config/environment.json')
        meta = self.load_file('config/stories.json')
        self.stories = meta['stories']
        self.entrypoint = meta['entrypoint']
        self.services = self.load_file('config/services.json')
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
