# -*- coding: utf-8 -*-
import asyncio
import time

from .Mutations import Mutations
from .Services import Services
from .. import Metrics
from ..Exceptions import InvalidKeywordUsage, \
    StoryscriptError, StoryscriptRuntimeError
from ..Story import Story
from ..Types import StreamingService
from ..constants import ContextConstants
from ..constants.LineConstants import LineConstants
from ..constants.LineSentinels import LineSentinels, ReturnSentinel
from ..utils import Resolver


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
    async def execute_line(logger, story, line_number):
        """
        Executes a single line by calling the Lexicon for various operations.

        To execute a function completely, see Lexicon#call.

        :return: Returns the next line number to be executed
        (return value from Lexicon), or None if there is none.
        """
        line: dict = story.line(line_number)
        story.start_line(line_number)

        with story.new_frame(line_number):
            try:
                method = line['method']
                if method == 'if' or method == 'else' or method == 'elif':
                    return await Lexicon.if_condition(logger, story, line)
                elif method == 'for':
                    return await Lexicon.for_loop(logger, story, line)
                elif method == 'execute':
                    return await Lexicon.execute(logger, story, line)
                elif method == 'set' or method == 'expression' \
                        or method == 'mutation':
                    return await Lexicon.set(logger, story, line)
                elif method == 'call':
                    return await Lexicon.call(logger, story, line)
                elif method == 'function':
                    return await Lexicon.function(logger, story, line)
                elif method == 'when':
                    return await Lexicon.when(logger, story, line)
                elif method == 'return':
                    return await Lexicon.ret(logger, story, line)
                elif method == 'break':
                    return await Lexicon.break_(logger, story, line)
                elif method == 'continue':
                    return await Lexicon.continue_(logger, story, line)
                elif method == 'while':
                    return await Lexicon.while_(logger, story, line)
                elif method == 'try':
                    return await Lexicon.try_catch(logger, story, line)
                elif method == 'throw':
                    return await Lexicon.throw(logger, story, line)
                else:
                    raise NotImplementedError(
                        f'Unknown method to execute: {method}'
                    )
            except BaseException as e:
                # Don't wrap StoryscriptError.
                if isinstance(e, StoryscriptError):
                    e.story = story  # Always set.
                    e.line = line  # Always set.
                    raise e

                raise StoryscriptRuntimeError(
                    message='Failed to execute line',
                    story=story, line=line, root=e)

    @staticmethod
    async def execute_block(logger, story, parent_line: dict):
        """
        Executes all the lines whose parent is parent_line, and returns
        either one of the following:
        1. A sentinel (from LineSentinels) - if this was returned by execute()
        2. None in all other cases

        The result can have special significance, such as the BREAK
        line sentinel.
        """
        next_line = story.line(parent_line['enter'])

        # If this block represents a streaming service, copy over it's
        # output to the context, so that Lexicon can read it later.
        if parent_line.get('output') is not None \
                and parent_line.get('method') == 'when':
            story.context[ContextConstants.service_output] = \
                parent_line['output'][0]

            if story.context.get(ContextConstants.service_event) is not None:
                story.context[parent_line['output'][0]] = \
                    story.context[ContextConstants.service_event].get('data')

        while next_line is not None \
                and story.line_has_parent(parent_line['ln'], next_line):
            result = await Lexicon.execute_line(logger, story, next_line['ln'])

            if LineSentinels.is_sentinel(result):
                return result

            next_line = story.line(result)

        return None

    @staticmethod
    async def function(logger, story, line):
        """
        Functions are not executed when they're encountered.
        This method returns the next block's line number,
        if there are more statements to be executed.
        """
        return Lexicon.line_number_or_none(story.next_block(line))

    @staticmethod
    async def call(logger, story, line):
        """
        Calls a particular function indicated by the line.
        This will setup a new context for the
        function block to be executed, and will return the output (if any).
        """
        current_context = story.context
        function_line = story.function_line_by_name(line.get('function'))
        context = story.context_for_function_call(line, function_line)
        return_from_function_call = None
        try:
            story.set_context(context)
            result = await Lexicon.execute_block(logger, story, function_line)
            if LineSentinels.is_sentinel(result):
                if not isinstance(result, ReturnSentinel):
                    raise StoryscriptRuntimeError(
                        f'Uncaught sentinel has'
                        f' escaped! sentinel={result}'
                    )

                return_from_function_call = result.return_value

            return Lexicon.line_number_or_none(story.line(line.get('next')))
        finally:
            story.set_context(current_context)
            if line.get('name') is not None and len(line['name']) > 0:
                story.end_line(line['ln'],
                               output=return_from_function_call,
                               assign={
                                   '$OBJECT': 'path', 'paths': line['name']})

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
    async def continue_(logger, story, line):
        # Ensure that we're in a foreach loop. If we are, return CONTINUE,
        # otherwise raise an exception.
        if Lexicon._does_line_have_parent_method(story, line, 'for') or \
                Lexicon._does_line_have_parent_method(story, line, 'while'):
            return LineSentinels.CONTINUE
        else:
            # There is no parent, this is an illegal usage of continue.
            raise InvalidKeywordUsage(story, line, 'continue')

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
                raise StoryscriptError(
                    message=f'Unsupported argument in set: '
                    f'{line["args"][1]["$OBJECT"]}',
                    story=story, line=line)

        story.end_line(line['ln'], output=value,
                       assign={'$OBJECT': 'path', 'paths': line['name']})
        return Lexicon.line_number_or_none(story.line(line.get('next')))

    @staticmethod
    def _is_if_condition_true(story, line):
        if len(line['args']) != 1:
            raise StoryscriptError(
                message=f'Complex if condition found! '
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
    async def try_catch(logger, story, line):
        """
        Executes the try/catch/finally construct. If any StoryscriptError
        exception is thrown by the try block, the catch block will be
        invoked. However, if the error is not of type StoryscriptError,
        then it will be thrown up directly - in this case, the finally
        block will not be executed either (since the error that
        occurred is not a StoryscriptError, but rather a programming
        error in the runtime).

        :return: Returns the line to be executed immediately after
        the catch block or finally block.
        """
        next_line = story.next_block(line)

        if next_line is None:
            return None

        async def next_block_or_finally():
            """
            This will execute if the next block is a finally block.
            It happens because the lexicon should always execute
            a finally block when there's a StoryscriptError

            :return: Returns the next line to be executed.
            """
            if next_line['method'] != 'finally':
                last_block = story.next_block(next_line)
            else:
                last_block = next_line

            if last_block is not None and \
                    last_block['method'] == 'finally':
                await Lexicon.execute_block(logger, story,
                                            last_block)
                last_block = story.next_block(last_block)

            return Lexicon.line_number_or_none(last_block)

        try:
            await Lexicon.execute_block(logger, story, line)
        except StoryscriptError as e:
            if next_line['method'] == 'finally':
                # skip right to the finally block
                return await next_block_or_finally()

            try:
                await Lexicon.execute_block(logger, story, next_line)
            except StoryscriptError as re:
                # if the catch block contains a StoryscriptError,
                # we must catch it, and run the finally
                # block anyway, followed up by raising the
                # exception
                await next_block_or_finally()
                raise re

        return await next_block_or_finally()

    @staticmethod
    def throw(logger, story, line):
        if line['args'] is not None and \
                len(line['args']) > 0:
            err_str = story.resolve(line['args'][0])
        else:
            err_str = None

        raise StoryscriptError(message=err_str, story=story, line=line)

    @staticmethod
    async def for_loop(logger, story, line):
        """
        Evaluates a for loop.
        """
        _list = story.resolve(line['args'][0], encode=False)
        output = line['output'][0]

        try:
            for item in _list:
                story.context[output] = item

                result = await Lexicon.execute_block(logger, story, line)

                if LineSentinels.BREAK == result:
                    break
                if LineSentinels.CONTINUE == result:
                    continue
                elif LineSentinels.is_sentinel(result):
                    # We do not know what to do with this sentinel,
                    # so bubble it up.
                    return result
        finally:
            # Don't leak the variable to the outer scope.
            del story.context[output]

        # Use story.next_block(line), because line["exit"] is unreliable...
        return Lexicon.line_number_or_none(story.next_block(line))

    @staticmethod
    async def while_(logger, story, line):
        call_count = 0
        while Resolver.resolve(line['args'][0], story.context):
            # note this is only a temporary solution,
            # and we will address this in the future.
            if call_count >= 100000:
                raise StoryscriptRuntimeError(
                    message='Call count limit reached within while loop. '
                            'Only 100000 iterations allowed.',
                    story=story, line=line
                )

            result = await Lexicon.execute_block(logger, story, line)

            if call_count % 10 == 0:
                # Let's sleep so we don't take up 100% of the CPU
                await asyncio.sleep(0.0002)

            call_count += 1

            if result == LineSentinels.CONTINUE:
                continue
            elif result == LineSentinels.BREAK:
                break
            elif LineSentinels.is_sentinel(result):
                return result

        return Lexicon.line_number_or_none(story.next_block(line))

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
            raise StoryscriptError(
                message=f'Unknown service {service} for when!',
                story=story, line=line)

    @classmethod
    async def ret(cls, logger, story: Story, line):
        """
        Implementation for return.
        The semantics for return are as follows:
        1. Stops execution and returns from the nearest when or function block

        Returns can happen in two types of blocks:
        1. From when blocks - no value may be returned
        2. From function blocks - one value may be returned
        """
        args = line.get('args', line.get('arguments'))
        if args is None:
            args = []

        if cls._does_line_have_parent_method(story, line, 'when'):
            assert len(args) == 0, \
                'return may not be used with a value in a when block'

            return LineSentinels.RETURN
        elif cls._does_line_have_parent_method(story, line, 'function'):
            returned_value = None

            if len(args) > 0:
                assert len(args) == 1, 'multiple return values are not allowed'
                returned_value = story.resolve(args[0])

            return ReturnSentinel(return_value=returned_value)
        else:
            # There is no parent, this is an illegal usage of return.
            raise InvalidKeywordUsage(story, line, 'return')
