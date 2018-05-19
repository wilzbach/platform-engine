# -*- coding: utf-8 -*-
from .Lexicon import Lexicon


class Handler:
    """
    Handles various task-related things.
    """

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
        elif line['method'] == 'run':
            return Lexicon.run(logger, story, line)
        elif line['method'] == 'set':
            return Lexicon.set(logger, story, line)
