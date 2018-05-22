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

    def line_has_parent(self, parent_line_number, line):
        """
        Looks up the hierarchy of this line to see if it
        belongs to a particular parent.

        :param parent_line_number: The parent line number
        :param line: The line to test
        :return: True if this line is a child of the parent (directly or
                 indirectly), False otherwise
        """

        # Fast test - this line is an immediate child of the parent.
        if parent_line_number == line.get('parent', None):
            return True

        while line is not None:
            my_parent_number = line.get('parent', None)

            if my_parent_number is None:
                return False

            if my_parent_number == parent_line_number:
                return True

            line = self.line(my_parent_number)

        return False

    def child_block(self, parent_line_number):
        """
        Slices the story to a single block with the same parent. Used when
        running a single block of the story, for example when the story is
        being resumed.
        """
        dictionary = {}
        for key, value in self.tree.items():
            if self.line_has_parent(parent_line_number, value):
                dictionary[key] = value
        self.tree = dictionary

    def next_block(self, parent_line):
        """
        Given a parent_line, it skips through the block and returns the next
        line after this block.
        """
        next_line = parent_line

        while next_line is not None:
            next_line = self.next_line(next_line['ln'])

            if next_line is None:
                return None

            # See if the next line is a block. If it is, skip through it.
            if next_line.get('enter', None) is not None:
                next_line = self.next_block(next_line)

                if next_line is None:
                    return None

            if next_line.get('parent', None) != parent_line['ln']:
                break

        return next_line

    def is_command(self, container, argument):
        """
        Checks whether argument is a command for the given container
        """
        if type(argument) is str or self.containers is None:
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
        # TODO 09/05/2018: Look up asyncy.yml for this container,
        # and build the command.
        if line['container'] == 'http-endpoint':
            return line['container']

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

    def argument_by_name(self, line, argument_name):
        args = line['args']
        if args is None:
            return None

        for arg in args:
            if arg['$OBJECT'] == 'argument' and \
                    arg['name'] == argument_name:
                return self.resolve(arg['argument'])

        return None

    def prepare(self, context=None, start=None, block=None):
        if context is None:
            context = {}

        self.context = context

        self.context['env'] = self.app.environment['env']

        if start:
            self.start_from(start)
        if block:
            self.child_block(block)
