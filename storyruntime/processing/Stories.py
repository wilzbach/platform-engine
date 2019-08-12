# -*- coding: utf-8 -*-
import time

from .. import Metrics
from ..Exceptions import StoryscriptError
from ..Exceptions import StoryscriptRuntimeError
from ..Story import Story
from ..constants.ContextConstants import ContextConstants
from ..constants.LineSentinels import LineSentinels
from ..processing import Lexicon


class Stories:

    @staticmethod
    def story(app, logger, story_name):
        return Story(app, story_name, logger)

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
            result = await Lexicon.execute_line(logger, story, line_number)

            # Sentinels are not allowed to escape from here.
            if LineSentinels.is_sentinel(result):
                raise StoryscriptRuntimeError(
                    message=f'A sentinel has escaped ({result})!',
                    story=story, line=story.line(line_number))

            line_number = result
            logger.log('story-execution', line_number)

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
                raise StoryscriptRuntimeError('No longer supported')
            elif block:
                with story.new_frame(block):
                    await Lexicon.execute_block(logger, story,
                                                story.line(block))
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
