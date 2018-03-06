# -*- coding: utf-8 -*-


class Lexicon:
    """
    Lexicon of possible line actions and their implementation
    """

    @staticmethod
    def if_condition(logger, story, line):
        """
        Evaluates the resolution value to decide wheter to enter
        inside an if-block.
        """
        result = story.resolve(logger, line['ln'])
        if result[0]:
            return line['enter']
        return line['exit']

    @staticmethod
    def unless_condition(logger, story, line):
        result = story.resolve(logger, line['ln'])
        if result[0]:
            return line['exit']
        return line['enter']

    @staticmethod
    def next(command):
        if command.endswith('.story'):
            return command
        return '{}.story'.format(command)
