# -*- coding: utf-8 -*-
import pathlib
import time
import uuid
from json import JSONDecodeError, dumps, loads

from .utils import Dict
from .utils.Resolver import Resolver


class Stories:

    def __init__(self, app, story_name, logger):
        self.app = app
        self.name = story_name
        self.logger = logger
        self.tree = app.stories[story_name]['tree']
        self.entrypoint = app.stories[story_name]['entrypoint']
        self.results = {}
        self.environment = None
        self.context = None
        self.containers = None
        self.repository = None
        self.version = None
        self.execution_id = str(uuid.uuid4())
        self._tmp_dir_created = False

    def create_tmp_dir(self):
        if self._tmp_dir_created:
            return

        self._tmp_dir_created = True

        path = self.get_tmp_dir()
        pathlib.Path(path).mkdir(parents=True, mode=0o700, exist_ok=True)
        self.logger.debug(f'Created tmp dir {path} (on-demand)')

    def get_tmp_dir(self):
        return f'/tmp/story.{self.execution_id}'

    def line(self, line_number):
        if line_number is None:
            return None

        return self.tree[line_number]

    def first_line(self):
        return self.entrypoint

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

    def next_block(self, parent_line: dict):
        """
        Given a parent_line, it skips through the block and returns the next
        line after this block.
        """
        next_line = parent_line

        while next_line.get('next') is not None:
            next_line = self.line(next_line['next'])

            # See if the next line is a block. If it is, skip through it.
            if next_line.get('enter', None) is not None \
                    and next_line.get('parent') == parent_line['ln']:
                next_line = self.next_block(next_line)

                if next_line is None:
                    return None

            if next_line.get('parent', None) != parent_line['ln']:
                break

        # We might have skipped through all the lines in this story,
        # and ended up on on the last line.
        # If this last line belongs to the same parent, then return None.
        # This check is required because the while loop breaks when it can't
        # find a next line.
        if next_line.get('parent') is not None \
                and self.line_has_parent(parent_line['ln'], next_line):
            return None

        # If the next_line == parent_line, then there weren't any more lines
        # after the parent.
        if next_line['ln'] == parent_line['ln']:
            return None

        return next_line

    def resolve(self, arg, encode=False):
        """
        Resolves line argument to their real value
        """
        if isinstance(arg, (str, int, float, bool)):
            self.logger.log('story-resolve', arg, arg)
            return arg

        result = Resolver.resolve(arg, self.context)

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

    def start_line(self, line_number):
        self.results[line_number] = {'start': time.time()}

    def end_line(self, line_number, output=None, assign=None):
        start = self.results[line_number]['start']

        # Please see https://github.com/asyncy/platform-engine/issues/148
        # for the rationale on removing auto conversion. Code commented and
        # NOT removed so that this note here makes sense.
        # if isinstance(output, str):
        #     try:
        #         # try to load it as json
        #         output = loads(output)
        #     except JSONDecodeError:
        #         # strip the string of tabs, spaces, newlines
        #         output = output.strip()

        if isinstance(output, str):
            output = output.strip()

        dictionary = {'output': output, 'end': time.time(), 'start': start}
        self.results[line_number] = dictionary

        # assign a variable to the output
        if assign:
            self.set_variable(assign, output)

    def set_variable(self, assign, output):
        Dict.set(self.context, assign['paths'], output)

    def function_line_by_name(self, function_name):
        """
        Finds the line which declares a function by the name of `function_name`
        and returns it.

        If no such function could be found, it returns None.
        """
        next_line = self.line(self.first_line())
        while next_line is not None:
            if next_line.get('method', None) == 'function':
                if next_line['function'] == function_name:
                    return next_line

            next_line = self.next_block(next_line)

        return None

    def argument_by_name(self, line, argument_name, encode=False):
        args = line.get('args')
        if args is None:
            return None

        for arg in args:
            if arg['$OBJECT'] == 'argument' and \
                    arg['name'] == argument_name:
                return self.resolve(arg['argument'], encode=encode)

        return None

    def context_for_function_call(self, line, function_line):
        """
        Prepares a new context for calling a function.
        This context consists of the arguments required by the function,
        and is copied over in a new map. As a result, the nature of function
        calls in Storyscript is call by value.

        Functions are executed in the following manner:
        1. Prepare a new context for the function
        2. Temporarily switch Stories#context to this new context
        3. Execute the function block
        4. Restore the original Stories#context and continue execution

        :return: A new context, which contains the arguments required (if any)
        """
        new_context = {}
        args = function_line.get('args', [])
        for arg in args:
            if arg['$OBJECT'] == 'argument':
                arg_name = arg['name']
                actual = self.argument_by_name(line, arg_name)
                Dict.set(new_context, [arg_name], actual)

        return new_context

    def set_context(self, context):
        self.context = context or {}
        # Optimise this later.
        self.context['app'] = self.app.app_context.copy()

    def prepare(self, context=None):
        self.set_context(context)
        self.environment = self.app.environment or {}
