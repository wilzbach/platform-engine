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

    def is_command(self, container, argument):
        """
        Checks whether argument is a command for the given container
        """
        if argument['$OBJECT'] == 'path':
            path = argument['paths'][0]
            if path in self.containers[container]['commands']:
                return True

    def resolve(self, args):
        """
        Resolves line arguments to their real value
        """
        result = Resolver.resolve(args, self.environment)
        self.logger.log('story-resolve', args, result)
        return result

    def argument_format_type(self, argument_type):
        if argument_type == 'string':
            return '"{}"'
        return '{}'

    def command_arguments_string(self, container, command):
        string = []
        items = self.containers[container]['commands'][command]['args'].items()
        for name, argument_type in items:
            string.append(self.argument_format_type(argument_type))
        return ' '.join(string)

    def command_arguments_list(self, arguments):
        results = []
        for argument in arguments:
            results.append(self.resolve(argument))
        return results

    def resolve_command(self, line):
        """
        Resolves arguments for a container line to produce a command
        that can be passed to docker
        """
        if self.is_command(line['container'], line['args'][0]):
            command = line['args'][0]['paths'][0]
            arguments_string = self.command_arguments_string(line['container'],
                                                             command)
            arguments_list = self.command_arguments_list(line['args'][1:])
            string = '{} {}'.format(command, arguments_string)
            return string.format(*arguments_list)
        return self.resolve(line['args'])

    def start_line(self, line_number):
        self.results[line_number] = {'start': time.time()}

    def end_line(self, line_number, output=None):
        start = self.results[line_number]['start']
        dictionary = {'output': output, 'end': time.time(), 'start': start}
        self.results[line_number] = dictionary
