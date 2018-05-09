# -*- coding: utf-8 -*-
from asyncy.processing import Story

from asyncy.Exceptions import ArgumentNotFoundError
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

        """
        If the command is http-endpoint (a special service), then register
        the http method along with the path with the Server (also line).
        
        The Server will then make a RPC call back to engine on an actual HTTP
        request, passing along the line to start executing from.
        """
        if command == 'http-endpoint':
            # TODO 09/05/2018: Resolve argument "paths".
            # Need more clarity from @vesuvium.
            method = Lexicon.argument_by_name(line, 'method')
            if method is None:
                raise ArgumentNotFoundError(name='method')

            path = Lexicon.argument_by_name(line, 'path')
            if path is None:
                raise ArgumentNotFoundError(name='path')

            Story.register_http_endpoint(
                story_name=story.name, method=method,
                path=path, line=line['next']
            )

            # TODO 09/05/2018: Here, you can skip until the end of the current
            # block, and start processing from there.
            # TODO 09/05/2018: Check wih @steve.
            return None

        if command == 'log':
            story.end_line(line['ln'])
            next_line = story.next_line(line['ln'])
            if next_line:
                return next_line['ln']
            return None
        output = Containers.exec(logger, story, line['container'], command)
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
            Lexicon.run(logger, story, line['ln'])
        return line['exit']

    @staticmethod
    def argument_by_name(line, argument_name):
        args = line['args']
        if args is None:
            return None

        for arg in args:
            if arg['name'] == argument_name:
                return arg

        return None

    @staticmethod
    def next(logger, story, line):
        result = story.resolve(line['args'][0])
        if result.endswith('.story'):
            return result
        return '{}.story'.format(result)

    @staticmethod
    def wait(logger, story, line):
        logger.log('lexicon-wait-err', line)
        raise NotImplementedError
        # waiting_time = story.resolve(line['args'][0])
        # eta = dateparser.parse('in {}'.format(waiting_time))
        # kwargs = {'block': line['ln'], 'environment': story.environment}
        # current_app.send_task('asyncy.CeleryTasks.process_story',
        #                       args=[story.app_id, story.name], kwargs=kwargs,
        #                       eta=eta)
        # next_line = story.next_line(line['exit'])
        # story.end_line(line['ln'])
        # if next_line:
        #     return next_line['ln']
