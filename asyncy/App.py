# -*- coding: utf-8 -*-
import os
from json import load

from raven.contrib.tornado import AsyncSentryClient


class App:

    environment = {}
    stories = {}
    services = {}
    sentry_client = None

    def __init__(self, config, beta_user_id=None,
                 sentry_dsn=None, release=None):
        self.apply()
        self.config = config
        self.beta_user_id = beta_user_id

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
