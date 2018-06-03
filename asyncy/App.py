# -*- coding: utf-8 -*-
import os
from json import load

from .processing import Story


class App:

    environment = {}
    stories = {}
    services = {}

    def __init__(self, config):
        self.apply()
        self.config = config

    def load_file(self, filepath):
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

    def bootstrap(self):
        """
        Executes all the stories.
        This enables the story to listen to pub/sub,
        register with the gateway, and queue cron jobs.
        """
        for story_name in self.stories:
            Story.story(self, logger, story_name)