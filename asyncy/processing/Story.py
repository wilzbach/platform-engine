# -*- coding: utf-8 -*-
import time

from .. import Metrics
from ..Containers import Containers
from ..Exceptions import AsyncyError
from ..Stories import Stories
from ..constants.ContextConstants import ContextConstants
from ..constants.LineConstants import LineConstants
from ..constants.ServiceConstants import ServiceConstants
from ..processing import Lexicon
from ..utils import Dict


class Story:

    @staticmethod
    def story(app, logger, story_name):
        return Stories(app, story_name, logger)

    @staticmethod
    def save(logger, story, start):
        """
        Saves the narration and the results for each line.
        """
        logger.log('story-save', story.name, story.app_id)

    @staticmethod
    async def execute(logger, story):
        """
        Executes each line in the story
        """
        line_number = story.first_line()
        while line_number:
            line_number = await Story.execute_line(logger, story, line_number)
            logger.log('story-execution', line_number)

    @staticmethod
    async def execute_line(logger, story, line_number):
        """
        Executes a single line by calling the Lexicon for various operations.

        To execute a function completely, see Story#execute_function.

        :return: Returns the next line number to be executed
        (return value from Lexicon), or None if there is none.
        """
        line = story.line(line_number)
        story.start_line(line_number)
        try:
            method = line['method']
            if method == 'if':
                return await Lexicon.if_condition(logger, story, line)
            elif method == 'for':
                return await Lexicon.for_loop(logger, story, line)
            elif method == 'execute':
                return await Lexicon.execute(logger, story, line)
            elif method == 'set':
                return await Lexicon.set(logger, story, line)
            elif method == 'call':
                return await Story.execute_function(logger, story, line)
            elif method == 'function':
                return await Lexicon.function(logger, story, line)
            elif method == 'when':
                return await Lexicon.when(logger, story, line)
            else:
                raise NotImplementedError(
                    f'Unknown method to execute: {method}'
                )
        except BaseException as e:
            if isinstance(e, AsyncyError):  # Don't wrap AsyncyError.
                raise e

            raise AsyncyError(message='Failed to execute line',
                              story=story, line=line)

    @staticmethod
    async def execute_function(logger, story, line):
        """
        Calls a particular function indicated by the line.
        The parameter types are verified, and ensures that all the required
        parameters are present. This will setup a new context for the
        function block to be executed, and will return the output (if any).
        """
        current_context = story.context
        function_line = story.function_line_by_name(line['function'])
        context = story.context_for_function_call(line, function_line)
        try:
            story.set_context(context)
            await Story.execute_block(logger, story, function_line)
        finally:
            story.set_context(current_context)

    @staticmethod
    async def execute_block(logger, story, parent_line):
        """
        Executes all the lines whose parent is parent_line.
        """
        next_line = story.line(parent_line['enter'])

        # If this block represents a streaming service, copy over it's
        # output to the context, so that Lexicon can read it later.
        if parent_line.get('output') is not None:
            story.context[ContextConstants.service_output] = \
                parent_line['output'][0]

            if story.context.get(ContextConstants.service_event) is not None:
                story.context[parent_line['output'][0]] = \
                    story.context[ContextConstants.service_event].get('data')

        while next_line is not None and \
                next_line['parent'] == parent_line['ln']:
            if next_line.get('enter') is not None:
                await Story.execute_block(logger, story, next_line)
                next_line = story.next_block(next_line)
            else:
                await Story.execute_line(logger, story, next_line['ln'])
                next_line = story.line(next_line.get('next'))

    @classmethod
    async def run(cls,
                  app, logger, story_name, *, story_id=None,
                  block=None, context=None,
                  function_name=None):
        start = time.time()
        try:
            logger.log('story-start', story_name, story_id)

            story = cls.story(app, logger, story_name)
            story.prepare(context)

            if function_name:
                function_line = story.function_line_by_name(function_name)
                await cls.execute_function(logger, story, function_line)
            elif block:
                await cls.execute_block(logger, story, story.line(block))
            else:
                await cls.execute(logger, story)

            logger.log('story-end', story_name, story_id)
            Metrics.story_run_success.labels(app_id=app.app_id,
                                             story_name=story_name) \
                .observe(time.time() - start)
        except BaseException as err:
            Metrics.story_run_failure.labels(app_id=app.app_id,
                                             story_name=story_name) \
                .observe(time.time() - start)
            raise err
        finally:
            Metrics.story_run_total.labels(app_id=app.app_id,
                                           story_name=story_name) \
                .observe(time.time() - start)

    @classmethod
    async def destroy(cls, app, logger, story_name):
        """
        Destroys all containers that were created.
        For destroying subscriptions, see App#destroy.
        """
        story = cls.story(app, logger, story_name)
        line = story.line(story.first_line())
        while line is not None:
            if line[LineConstants.method] == 'execute':
                service = line[LineConstants.service]
                if app.services.get(service) is not None:
                    command = line[LineConstants.command]
                    run = Dict.find(app.services,
                                    f'{service}.{ServiceConstants.config}.'
                                    f'commands.{command}.run')
                    if run is not None:
                        c_name = Containers.get_container_name(story, line,
                                                               service)
                        await Containers.stop_container(story, line, c_name)

            line = story.line(line.get('next'))
