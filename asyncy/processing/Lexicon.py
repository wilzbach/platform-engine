# -*- coding: utf-8 -*-

from .internal.HttpEndpoint import HttpEndpoint
from ..Containers import Containers
from ..Exceptions import ArgumentNotFoundError
from ..constants.ContextConstants import ContextConstants


class Lexicon:
    """
    Lexicon of possible line actions and their implementation
    """

    @staticmethod
    async def run(logger, story, line):
        """
        Runs a container with the resolution values as commands
        """
        container = line['container']
        if container == 'http-endpoint':
            """
            If the container is http-endpoint (a special service),
            then register the http method along with the path with the Server
            (also line). The Server will then make a HTTP call back to engine
            on an actual HTTP request, passing along the line to
            start executing from.
            """
            method = Lexicon.argument_by_name(story, line, 'method')
            if isinstance(method, str) is False:
                raise ArgumentNotFoundError(name='method',
                                            story=story, line=line)

            path = Lexicon.argument_by_name(story, line, 'path')
            if isinstance(path, str) is False:
                raise ArgumentNotFoundError(name='path',
                                            story=story, line=line)

            await HttpEndpoint.register_http_endpoint(
                story=story, line=line, method=method,
                path=path, block=line['ln']
            )

            next_line = story.next_block(line)
            return Lexicon.next_line_or_none(next_line)
        elif story.context.get(ContextConstants.server_request) is not None \
                and (container == 'request' or container == 'response'):
            output = HttpEndpoint.run(story, line)
            story.end_line(line['ln'], output=output,
                           assign=line.get('output'))
            return Lexicon.next_line_or_none(story.line(line.get('next')))
        else:
            command = story.resolve_command(line)

            if command == 'log':
                story.end_line(line['ln'])
                return Lexicon.next_line_or_none(story.line(line.get('next')))

            container = line['container']
            output = await Containers.exec(logger, story, line,
                                           container, command)
            story.end_line(line['ln'], output=output,
                           assign=line.get('output'))

            return Lexicon.next_line_or_none(story.line(line.get('next')))

    @staticmethod
    async def function(logger, story, line):
        """
        Functions are not executed when they're encountered.
        This method returns the next block's line number,
        if there are more statements to be executed.
        """
        return Lexicon.next_line_or_none(story.next_block(line))

    @staticmethod
    def next_line_or_none(line):
        if line:
            return line['ln']

        return None

    @staticmethod
    async def set(logger, story, line):
        value = story.resolve(line['args'][1])
        story.end_line(line['ln'], output=value, assign=line['args'][0])
        return Lexicon.next_line_or_none(story.line(line.get('next')))

    @staticmethod
    async def if_condition(logger, story, line):
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
    async def for_loop(logger, story, line):
        """
        Evaluates a for loop
        """
        _list = story.resolve(line['args'][1], encode=False)
        output = line['args'][0]
        for item in _list:
            story.context[output] = item
            await Lexicon.run(logger, story, line['ln'])
        return line['exit']

    @staticmethod
    def argument_by_name(story, line, argument_name):
        return story.argument_by_name(line, argument_name)
