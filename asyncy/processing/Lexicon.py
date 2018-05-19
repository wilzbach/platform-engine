# -*- coding: utf-8 -*-
from .internal.HttpEndpoint import HttpEndpoint
from ..Containers import Containers
from ..Exceptions import ArgumentNotFoundError


class Lexicon:
    """
    Lexicon of possible line actions and their implementation
    """

    @staticmethod
    def run(logger, story, line):
        """
        Runs a container with the resolution values as commands
        """
        container = line['container']
        if container == 'http-endpoint':
            """
            If the container is http-endpoint (a special service),
            then register the http method along with the path with the Server
            (also line). The Server will then make a RPC call back to engine
            on an actual HTTP request, passing along the line to
            start executing from.
            """
            method = Lexicon.argument_by_name(story, line, 'method')
            if isinstance(method, str) is False:
                raise ArgumentNotFoundError(name='method')

            path = Lexicon.argument_by_name(story, line, 'path')
            if isinstance(path, str) is False:
                raise ArgumentNotFoundError(name='path')

            HttpEndpoint.register_http_endpoint(
                story_name=story.name, method=method,
                path=path, parent_line=line['ln']
            )

            next_line = story.next_block(line)
            return Lexicon.next_line_or_none(next_line)
        elif story.context.get('__server_request__') and \
                (container is 'request' or container is 'response'):
            output = HttpEndpoint.run(story, line)
            story.end_line(line['ln'], output=output,
                           assign=line.get('output'))
            return Lexicon.next_line_or_none(story.next_line(line['ln']))
        else:
            command = story.resolve_command(line)

            if command == 'log':
                story.end_line(line['ln'])
                return Lexicon.next_line_or_none(story.next_line(line['ln']))

            output = Containers.exec(logger, story, line['container'], command)
            story.end_line(line['ln'], output=output,
                           assign=line.get('output'))

            return Lexicon.next_line_or_none(story.next_line(line['ln']))

    @staticmethod
    def next_line_or_none(line):
        if line:
            return line['ln']

        return None

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
    def argument_by_name(story, line, argument_name):
        args = line['args']
        if args is None:
            return None

        for arg in args:
            if arg['$OBJECT'] == 'argument' and \
                    arg['name'] == argument_name:
                return story.resolve(arg['argument'])

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
