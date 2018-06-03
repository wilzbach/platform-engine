# -*- coding: utf-8 -*-
import os
import traceback
from json import load

from raven.contrib.tornado import AsyncSentryClient

from .processing import Story


class App:

    environment = {}
    stories = {}
    services = {}
    sentry_client = None

    def __init__(self, config, logger, beta_user_id=None,
                 sentry_dsn=None, release=None):
        self.apply()
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

    def apply(self):
        """
        Build environment, stories, and services from start of service.
        """
        self.environment = self.load_file('environment.json')
        self.stories = self.load_file('stories.json')
        self.services = self.load_file('services.json')

    async def bootstrap(self):
        """
        Executes all the stories.
        This enables the story to listen to pub/sub,
        register with the gateway, and queue cron jobs.
        """
        for story_name in self.stories:
            try:
                await Story.run(self, self.logger, story_name)
            except Exception as e:
                traceback.print_exc()

    async def destroy(self):
        """
        Destroys all stories, one at a time.
        """
        for story_name in self.stories:
            try:
                await Story.destroy(self, self.logger, story_name)
            except Exception as e:
                traceback.print_exc()
