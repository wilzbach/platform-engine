# -*- coding: utf-8 -*-
from ..Containers import Containers


class Lexicon:
    """
    Lexicon of possible line actions and their implementation
    """

    @staticmethod
    def run(logger, story, line):
        """
        Runs a container with the resolution values as commands
        """
        command = story.resolve(line['args'])
        container = Containers(line['container'], logger)
        container.make_volume(story.name)
        container.run(command, story.environment)
        story.end_line(line['ln'], container.result())

    @staticmethod
    def set(logger, story, line):
        value = story.resolve(line['args'][1])
        story.environment[line['args'][0]['paths'][0]] = value
        return story.next_line(line['ln'])

    @staticmethod
    def if_condition(logger, story, line):
        """
        Evaluates the resolution value to decide wheter to enter
        inside an if-block.
        """
        result = story.resolve(line['args'])
        if result[0]:
            return line['enter']
        return line['exit']

    @staticmethod
    def unless_condition(logger, story, line):
        result = story.resolve(line['args'])
        if result[0]:
            return line['exit']
        return line['enter']

    @staticmethod
    def next(logger, story, line):
        result = story.resolve(line['args'])
        if result.endswith('.story'):
            return result
        return '{}.story'.format(result)
