# -*- coding: utf-8 -*-
from .Lexicon import Lexicon
from ..Mongo import Mongo


class Handler:
    """
    Handles various task-related things.
    """

    @staticmethod
    def init_mongo(mongo_url):
        return Mongo(mongo_url)

    @staticmethod
    def run(logger, line_number, story):
        """
        Run the story
        """
        line = story.line(line_number)
        story.start_line(line_number)

        if line['method'] == 'if':
            return Lexicon.if_condition(logger, story, line)
        elif line['method'] == 'for':
            return Lexicon.for_loop(logger, story, line)
        elif line['method'] == 'next':
            return Lexicon.next(logger, story, line)
        elif line['method'] == 'run':
            Lexicon.run(logger, story, line)
        elif line['method'] == 'set':
            return Lexicon.set(logger, story, line)
        elif line['method'] == 'wait':
            return Lexicon.wait(logger, story, line)
