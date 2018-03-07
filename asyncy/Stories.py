# -*- coding: utf-8 -*-
from .utils import Http


class Stories:

    def __init__(self, logger, app_id, story_name):
        self.app_id = app_id
        self.name = story_name
        self.logger = logger

    def get(self):
        url = 'http://api/apps/{}/stories/{}'.format(self.app_id, self.name)
        story = Http.get(url, json=True)
        self.tree = story['tree']
        self.environment = story['environment']
        self.containers = story['containers']
        self.repository = story['repository']
        self.version = story['version']
