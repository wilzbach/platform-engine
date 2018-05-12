# -*- coding: utf-8 -*-
import os
import time
from json import JSONDecodeError, dumps, loads

from storyscript.resolver import Resolver

from .utils import Dict


class Stories:

    def __init__(self, app, story_name, logger):
        self.app = app
        self.name = story_name
        self.logger = logger
        self.tree = app.stories[story_name]['tree']
        self.results = {}
        self.tree = None
        self.environment = None
        self.context = None
        self.containers = None
        self.repository = None
        self.version = None

    def line(self, line_number):
        return self.tree[line_number]

    def sorted_lines(self):
        """
        Returns sorted line numbers
        """
        return sorted(self.tree.keys(), key=lambda x: int(x))

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
            return self.tree[str(next_line)]

    def start_from(self, line):
        """
        Slices the story from the given line onwards.
        """
        sorted_lines = self.sorted_lines()
        i = sorted_lines.index(line)
        allowed_lines = sorted_lines[i:]
        dictionary = {}
        for line_number in allowed_lines:
            dictionary[line_number] = self.tree[line_number]
        self.tree = dictionary

    def child_block(self, parent_line):
        """
        Slices the story to a single block with the same parent. Used when
        running a single block of the story, for example when the story is
        being resumed.
        """
        dictionary = {}
        for key, value in self.tree.items():
            if 'parent' in value:
                if value['parent'] == parent_line:
                    dictionary[key] = value
        self.tree = dictionary

    def is_command(self, container, argument):
        """
        Checks whether argument is a command for the given container
        """
        if type(argument) is str:
            return None

        if argument['$OBJECT'] == 'path':
            if len(argument['paths']) == 1:
                path = argument['paths'][0]
                if path in self.containers[container]['commands']:
                    return True

    def resolve(self, arg, encode=False):
        """
        Resolves line argument to their real value
        """
        if isinstance(arg, (str, int, float, bool)):
            self.logger.log('story-resolve', arg, arg)
            return arg

        # patch for $OBJECT=file
        is_file = (
            isinstance(arg, dict) and
            (arg['$OBJECT'] == 'file' or arg.get('type') == 'file')
        )
        # end patch

        result = Resolver.resolve(arg, self.context)

        # patch for $OBJECT=file
        if is_file:
            result = os.path.join('/tmp/cache', result.lstrip('/'))
        # end patch

        self.logger.log('story-resolve', arg, result)
        # encode and escape then format for shell
        if encode:
            return self.encode(result)
        else:
            return result

    def encode(self, arg):
        if arg is None or isinstance(arg, bool):
            return dumps(arg)
        elif isinstance(arg, (list, dict)):
            arg = dumps(arg)
        else:
            arg = str(arg)
        return "'%s'" % arg.replace("'", "\'")

    def command_arguments_list(self, arguments):
        results = []

        if arguments:
            arg = arguments[0]
            # if first path is undefined assume command
            if (
                isinstance(arg, dict) and
                arg['$OBJECT'] == 'path' and
                len(arg['paths']) == 1
            ):
                res = self.resolve(arguments.pop(0))
                if res is None:
                    results.append(arg['paths'][0])
                else:
                    results.append(self.encode(res))

        if arguments:
            for argument in arguments:
                results.append(self.resolve(argument, encode=True))

        return results

    def resolve_command(self, line):
        """
        Resolves arguments for a container line to produce a command
        that can be passed to docker
        """
        if line['container'] == 'log':
            args = line['args']
            if len(args) == 1:
                lvl = 'info'
                message = self.resolve(args[0])
            else:
                arguments = self.command_arguments_list(args)
                if arguments[0] not in ('info', 'warn', 'error', 'debug'):
                    lvl = 'info'
                else:
                    lvl = arguments.pop(0)
                message = ', '.join(arguments)

            self.logger.log_raw(lvl, message)
            return 'log'

        if self.is_command(line['container'], line['args'][0]):
            command = line['args'][0]['paths'][0]
            arguments_list = self.command_arguments_list(line['args'][1:])
            arguments_list.insert(0, command)
            return ' '.join(arguments_list)

        return ' '.join(self.command_arguments_list(line['args']))

    def start_line(self, line_number):
        self.results[line_number] = {'start': time.time()}

    def end_line(self, line_number, output=None, assign=None):
        start = self.results[line_number]['start']

        if type(output) is bytes:
            output = output.decode('utf-8')

        if not isinstance(output, (list, dict)) and output:
            try:
                # try to load it as json
                output = loads(output)
            except JSONDecodeError:
                # strip the string of tabs, spaces, newlines
                output = output.strip()

        dictionary = {'output': output, 'end': time.time(), 'start': start}
        self.results[line_number] = dictionary

        # assign a variable to the output
        if assign:
            Dict.set(self.context, assign['paths'], output)

    def prepare(self, context, start, block):
        if context is None:
            context = {}

        self.context = context

        self.context['env'] = self.app.environment['env']

        if start:
            self.start_from(start)
        if block:
            self.child_block(block)
