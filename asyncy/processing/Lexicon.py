# -*- coding: utf-8 -*-
import time

from .Mutations import Mutations
from .Services import Services
from .. import Metrics
from ..Exceptions import AsyncyError, InvalidKeywordUsage
from ..Stories import Stories
from ..Types import StreamingService
from ..constants.LineConstants import LineConstants
from ..constants.LineSentinels import LineSentinels


class Lexicon:
    """
    Lexicon of possible line actions and their implementation
    """

    @staticmethod
    async def execute(logger, story, line):
        """
        Runs a service with the resolution values as commands
        """
        service = line[LineConstants.service]

        start = time.time()

        if line.get('enter') is not None:
            """
            When a service to be executed has an 'enter' line number,
            it's a streaming service. Let's bring up the service and
            update the context with the output name.

            Example:
            foo stream as client
                when client grep:'bar' as result
                    # do something with result
            """
            output = await Services.start_container(story, line)
            Metrics.container_start_seconds_total.labels(
                app_id=story.app.app_id,
                story_name=story.name, service=service
            ).observe(time.time() - start)

            story.end_line(line['ln'], output=output,
                           assign={'paths': line.get('output')})

            return Lexicon.line_number_or_none(story.line(line.get('next')))
        else:
            output = await Services.execute(story, line)
            Metrics.container_exec_seconds_total.labels(
                app_id=story.app.app_id,
                story_name=story.name, service=service
            ).observe(time.time() - start)

            if line.get('name') and len(line['name']) == 1:
                story.end_line(line['ln'], output=output,
                               assign={'paths': line['name']})
            else:
                story.end_line(line['ln'], output=output,
                               assign=line.get('output'))

            return Lexicon.line_number_or_none(story.line(line.get('next')))

    @staticmethod
    async def function(logger, story, line):
        """
        Functions are not executed when they're encountered.
        This method returns the next block's line number,
        if there are more statements to be executed.
        """
        return Lexicon.line_number_or_none(story.next_block(line))

    @staticmethod
    def _does_line_have_parent_method(story, line, parent_method_wanted):
        # Just walk up the stack using 'parent'.
        while True:
            parent_line = line.get('parent')
            if parent_line is None:
                return False

            parent_line = story.line(parent_line)

            if parent_line['method'] == parent_method_wanted:
                return True
            else:
                line = parent_line

    @staticmethod
    async def break_(logger, story, line):
        # Ensure that we're in a foreach loop. If we are, return BREAK,
        # otherwise raise an exception.
        if Lexicon._does_line_have_parent_method(story, line, 'for'):
            return LineSentinels.BREAK
        else:
            # There is no parent, this is an illegal usage of break.
            raise InvalidKeywordUsage(story, line, 'break')

    @staticmethod
    def line_number_or_none(line):
        if line:
            return line['ln']

        return None

    @staticmethod
    async def set(logger, story, line):
        value = story.resolve(line['args'][0])

        if len(line['args']) > 1:
            # Check if args[1] is a mutation.
            if line['args'][1]['$OBJECT'] == 'mutation':
                value = Mutations.mutate(line['args'][1], value, story, line)
                logger.debug(f'Mutation result: {value}')
            else:
                raise AsyncyError(
                    message=f'Unsupported argument in set: '
                            f'{line["args"][1]["$OBJECT"]}',
                    story=story, line=line)

        story.end_line(line['ln'], output=value,
                       assign={'$OBJECT': 'path', 'paths': line['name']})
        return Lexicon.line_number_or_none(story.line(line.get('next')))

    @staticmethod
    def _is_if_condition_true(story, line):
        if len(line['args']) != 1:
            raise AsyncyError(message=f'Complex if condition found! '
                                      f'len={len(line["args"])}',
                              story=story, line=line)

        return story.resolve(line['args'][0], encode=False)

    @staticmethod
    async def if_condition(logger, story, line):
        """
        Evaluates the resolution value to decide whether to enter
        inside an if-block.

        Execution strategy:
        1. Evaluate the if condition. If true, return the 'enter' line number
        2. If the condition is false, find next elif, and perform step 1
        3. If we reach an else block, perform step 1 without condition check

        Since the entire if/elif/elif/else block execution happens here,
        we can ignore all subsequent elif/else calls, and just return the
        next block.
        """
        if line['method'] == 'elif' or line['method'] == 'else':
            # If something had to be executed in this if/elif/else block, it
            # would have been executed already. See execution strategy above.
            return Lexicon.line_number_or_none(story.next_block(line))

        # while true here because all if/elif/elif/else is executed here.
        while True:
            logger.log('lexicon-if', line, story.context)

            if line['method'] == 'else':
                result = True
            else:
                result = Lexicon._is_if_condition_true(story, line)

            if result:
                return line['enter']
            else:
                # Check for an elif block or an else block
                # (step 2 of execution strategy).
                next_line = story.next_block(line)
                if next_line is None:
                    return None

                # Ensure that the elif/else is in the same parent.
                if next_line.get('parent') == line.get('parent') and \
                        (next_line['method'] == 'elif' or
                         next_line['method'] == 'else'):
                    # Continuing this loop will mean that step 1 in the
                    # execution strategy is performed.
                    line = next_line
                    continue
                else:
                    # Next block is not a part of the if/elif/else.
                    return Lexicon.line_number_or_none(next_line)

        # Note: Control can NEVER reach here.

    @staticmethod
    def unless_condition(logger, story, line):
        logger.log('lexicon-unless', line, story.context)
        result = story.resolve(line['args'][0], encode=False)
        if result:
            return line['exit']
        return line['enter']

    @staticmethod
    async def for_loop(logger, story, line):
        """
        Evaluates a for loop.
        """
        _list = story.resolve(line['args'][0], encode=False)
        output = line['output'][0]

        from . import Story

        try:
            for item in _list:
                story.context[output] = item

                result = await Story.execute_block(logger, story, line)

                if LineSentinels.BREAK == result:
                    break
                elif LineSentinels.is_sentinel(result):
                    # We do not know what to do with this sentinel,
                    # so bubble it up.
                    return result
        finally:
            # Don't leak the variable to the outer scope.
            del story.context[output]

        return line['exit']

    @staticmethod
    async def when(logger, story, line):
        service = line[LineConstants.service]

        # Does this service belong to a streaming service?
        s = story.context.get(service)
        if isinstance(s, StreamingService):
            # Yes, we need to subscribe to an event with the service.
            await Services.when(s, story, line)
            next_line = story.next_block(line)
            return Lexicon.line_number_or_none(next_line)
        else:
            raise AsyncyError(message=f'Unknown service {service} for when!',
                              story=story, line=line)

    @classmethod
    async def ret(cls, logger, story: Stories, line):
        """
        Implementation for return.
        The semantics for return are as follows:
        1. Stops execution and returns from the nearest when or function block
        2. At this time, return from functions is not supported because
           we haven't spec'd it out completely.
           See https://github.com/storyscript/storyscript/issues/596

        As a result, only return in when blocks are supported, and cannot
        return any value (since when blocks return nothing).
        """
        args = line.get('args', line.get('arguments'))
        if args is not None and len(args) > 0:
            # No support for returning a value.
            raise AsyncyError('return may not be used with a value')

        if cls._does_line_have_parent_method(story, line, 'when'):
            return LineSentinels.RETURN
        else:
            # There is no parent, this is an illegal usage of return.
            raise InvalidKeywordUsage(story, line, 'return')
