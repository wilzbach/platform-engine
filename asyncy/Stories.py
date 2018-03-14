# -*- coding: utf-8 -*-
import time

from storyscript.resolver import Resolver

from .utils import Http


class Stories:

    def __init__(self, config, logger, app_id, story_name):
        self.app_id = app_id
        self.name = story_name
        self.config = config
        self.logger = logger
        self.results = {}

    def get(self):
        url_template = 'http://{}/apps/{}/stories/{}'
        url = url_template.format(self.config.api_url, self.app_id, self.name)
        story = Http.get(url, json=True)
        self.tree = story['tree']
        self.environment = story['environment']
        self.containers = story['containers']
        self.repository = story['repository']
        self.version = story['version']

    def line(self, line_number):
        return self.tree['script'][line_number]

    def sorted_lines(self):
        """
        Returns sorted line numbers
        """
        return sorted(self.tree['script'].keys(), key=lambda x: int(x))

    def first_line(self):
        """
        Finds the first line of a story. The tree can start at lines other
        than '1' so the first line is not obvious.
        """
        return self.sorted_lines()[0]

    def next_line(self, line_number):
        """
        Finds the next line from the current one.
        Storyscript does not always provide the next line explicitly, which
        is instead necessary in some cases.
        """
        sorted_lines = self.sorted_lines()
        next_line_index = sorted_lines.index(line_number) + 1
        if next_line_index < len(sorted_lines):
            next_line = sorted_lines[next_line_index]
            return self.tree['script'][str(next_line)]

    def child_block(self, parent_line):
        """
        Slices the story to a single block with the same parent. Used when
        running a single block of the story, for example when the story is
        being resumed.
        """
        dictionary = {}
        for key, value in self.tree['script'].items():
            if 'parent' in value:
                if value['parent'] == parent_line:
                    dictionary[key] = value
        self.tree['script'] = dictionary

    def resolve(self, args):
        """
        Resolves line arguments to their real value
        """
        result = Resolver.resolve(args, self.environment)
        self.logger.log('story-resolve', args, result)
        return result

    def start_line(self, line_number):
        self.results[line_number] = {'start': time.time()}

    def end_line(self, line_number, output):
        start = self.results[line_number]['start']
        dictionary = {'output': output, 'end': time.time(), 'start': start}
        self.results[line_number] = dictionary
