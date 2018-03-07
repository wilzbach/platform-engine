# -*- coding: utf-8 -*-
import time

from storyscript.resolver import Resolver

from .utils import Http


class Stories:

    def __init__(self, logger, app_id, story_name):
        self.app_id = app_id
        self.name = story_name
        self.logger = logger
        self.results = {}

    def get(self):
        url = 'http://api/apps/{}/stories/{}'.format(self.app_id, self.name)
        story = Http.get(url, json=True)
        self.tree = story['tree']
        self.environment = story['environment']
        self.containers = story['containers']
        self.repository = story['repository']
        self.version = story['version']

    def line(self, line_number):
        return self.tree['script'][line_number]

    def resolve(self, line_number):
        """
        Resolves line arguments to their real value
        """
        line = self.line(line_number)
        result = Resolver.resolve(line['args'], self.environment)
        self.logger.log('story-resolve', line['args'], result)
        return result

    def start_line(self, line_number):
        self.results[line_number] = {'start': time.time()}

    def end_line(self, line_number, output):
        start = self.results[line_number]['start']
        dictionary = {'output': output, 'end': time.time(), 'start': start}
        self.results[line_number] = dictionary
