# -*- coding: utf-8 -*-
from celery import current_app

import dateparser

from ..utils import Dict
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
        command = story.resolve_command(line)
        if command == 'log':
            story.end_line(line['ln'])
            next_line = story.next_line(line['ln'])
            if next_line:
                return next_line['ln']
            return None
        output = Containers.run(logger, story, line['container'], command)
        story.end_line(line['ln'], output=output, assign=line.get('output'))
        next_line = story.next_line(line['ln'])
        if next_line:
            return next_line['ln']

    @staticmethod
    def set(logger, story, line):
        value = story.resolve(line['args'][1])
        story.end_line(line['ln'], output=value, assign=line['args'][0])
        return story.next_line(line['ln'])['ln']

    @staticmethod
    def if_condition(logger, story, line):
        """
        Evaluates the resolution value to decide wheter to enter
        inside an if-block.
        """
        logger.log('lexicon-if', line, story.context)
        result = story.resolve(line['args'][0], encode=False)
        if result:
            return line['enter']
        return line['exit']

    @staticmethod
    def unless_condition(logger, story, line):
        logger.log('lexicon-unless', line, story.context)
        result = story.resolve(line['args'][0], encode=False)
        if result:
            return line['exit']
        return line['enter']

    @staticmethod
    def for_loop(logger, story, line):
        """
        Evaluates a for loop
        """
        _list = story.resolve(line['args'][1], encode=False)
        output = line['args'][0]
        for item in _list:
            story.context[output] = item
            kwargs = {'environment': story.environment,
                      'context': story.context, 'block': line['ln']}
            current_app.send_task('asyncy.CeleryTasks.process_story',
                                  args=[story.app_id, story.name],
                                  kwargs=kwargs, delay=0)
        return line['exit']

    @staticmethod
    def next(logger, story, line):
        result = story.resolve(line['args'][0])
        if result.endswith('.story'):
            return result
        return '{}.story'.format(result)

    @staticmethod
    def wait(logger, story, line):
        logger.log('lexicon-wait', line)
        waiting_time = story.resolve(line['args'][0])
        eta = dateparser.parse('in {}'.format(waiting_time))
        kwargs = {'block': line['ln'], 'environment': story.environment}
        current_app.send_task('asyncy.CeleryTasks.process_story',
                              args=[story.app_id, story.name], kwargs=kwargs,
                              eta=eta)
        next_line = story.next_line(line['exit'])
        story.end_line(line['ln'])
        if next_line:
            return next_line['ln']
