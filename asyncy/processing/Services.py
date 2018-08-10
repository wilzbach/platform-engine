# -*- coding: utf-8 -*-
import json
from collections import deque, namedtuple

from tornado.httpclient import AsyncHTTPClient

from ..Containers import Containers
from ..Exceptions import AsyncyError
from ..constants.LineConstants import LineConstants
from ..utils.HttpUtils import HttpUtils

InternalCommand = namedtuple('InternalCommand',
                             ['arguments', 'output_type', 'handler'])
InternalService = namedtuple('InternalService', ['commands'])

Service = namedtuple('Service', ['name'])
Command = namedtuple('Command', ['name'])
Event = namedtuple('Event', ['name'])


class Services:
    internal_services = {}
    logger = None

    @classmethod
    def register_internal(cls, name, command, arguments, output_type, handler):
        service = cls.internal_services.get(name)
        if service is None:
            service = InternalService(commands={})
            cls.internal_services[name] = service

        service.commands[command] = InternalCommand(arguments=arguments,
                                                    output_type=output_type,
                                                    handler=handler)

    @classmethod
    def is_internal(cls, service):
        return cls.internal_services.get(service) is not None

    @classmethod
    async def execute(cls, story, line):
        if cls.is_internal(line[LineConstants.service]):
            return await cls.execute_internal(story, line)
        else:
            return await cls.execute_external(story, line)

    @classmethod
    async def execute_internal(cls, story, line):
        service = cls.internal_services[line['service']]
        command = service.commands.get(line['command'])

        if command is None:
            raise AsyncyError(
                message=f'No command {line["command"]} '
                        f'for service {line["service"]}',
                story=story,
                line=line)

        resolved_args = {}

        if command.arguments:
            for arg in command.arguments:
                actual = story.argument_by_name(line=line, argument_name=arg)
                resolved_args[arg] = actual

        return await command.handler(story=story, line=line,
                                     resolved_args=resolved_args)

    @classmethod
    async def execute_external(cls, story, line):
        """
        Executes external services via HTTP or a docker exec.
        :return: The output of docker exec or the HTTP call.

        Note: If the Content-Type of an output from an HTTP call
        is application/json, this method will parse the response
        and return a dict.
        """
        service = line[LineConstants.service]
        chain = cls.resolve_chain(story, line)
        command_conf = cls.get_command_conf(story, chain)
        if command_conf.get('format') is not None:
            return await Containers.exec(story.logger, story, line,
                                         service, line['command'])
        elif command_conf.get('http') is not None:
            return await cls.execute_http(story, line, chain, command_conf)
        else:
            raise AsyncyError()  # TODO

    @classmethod
    def resolve_chain(cls, story, line):
        """
        resolve_chain returns a path (chain) to the current command.
        The command or service in 'line' might be the result of
        an event output, deeply nested. This method returns the
        path to the command described in line.

        Example:
        [Service(slack), Command(bot), Event(hears), Command(reply)]

        In most cases, the output would be:
        [Service(alpine), Command(echo)]

        The first entry in the chain will always be a concrete service,
        and the last entry will always be a command.
        """

        def get_owner(line):
            service = line[LineConstants.service]
            while True:
                parent = line.get(LineConstants.parent)
                if parent is None:
                    # In a perfect scenario, this is impossible.
                    # If this does occur, there's something wrong upstream.
                    return None

                line = story.line(parent)
                output = line.get(LineConstants.output)
                if output is not None \
                        and len(output) == 1 \
                        and service == output[0]:
                    return line

        chain = deque()
        parent_line = line

        while True:
            service = parent_line[LineConstants.service]

            if parent_line[LineConstants.method] == 'when':
                chain.appendleft(Event(parent_line[LineConstants.command]))
            else:
                chain.appendleft(Command(parent_line[LineConstants.command]))

            # Is this a concrete service?
            resolved = story.app.services.get(service)
            if resolved is not None:
                chain.appendleft(Service(service))
                break

            if parent_line.get(LineConstants.parent) is not None:
                parent_line = get_owner(parent_line)
            else:
                parent_line = None

            if parent_line is None:
                raise AsyncyError()  # TODO

        story.logger.debug(f'Chain resolved - {chain}')
        return chain

    @classmethod
    def get_command_conf(cls, story, chain):
        """
        Returns the conf for the command specified by 'chain'.
        """
        next = story.app.services
        for entry in chain:
            if isinstance(entry, Service):
                next = next[entry.name]['configuration']['commands']
            elif isinstance(entry, Command):
                next = next[entry.name]
            elif isinstance(entry, Event):
                next = next['events'][entry.name]['output']['commands']

        return next

    @classmethod
    async def execute_http(cls, story, line, chain, command_conf):
        assert isinstance(chain, deque)
        assert isinstance(chain[0], Service)
        hostname = await Containers.get_hostname(story, line, chain[0].name)
        args = command_conf.get('arguments')
        body = {}
        for arg in args:
            body[arg] = story.argument_by_name(line, arg)

        kwargs = {
            'method': command_conf['http'].get('method', 'post').upper(),
            # TODO support get params somehow
            'body': json.dumps(body),
            'headers': {
                'Content-Type': 'application/json; charset=utf-8'
            }
        }

        port = command_conf['http'].get('port', 5000)
        path = command_conf['http']['path']
        url = f'http://{hostname}:{port}{path}'

        story.logger.debug(f'Invoking service on {url} with payload {kwargs}')

        client = AsyncHTTPClient()
        response = await HttpUtils.fetch_with_retry(
            3, story.logger, url, client, kwargs)

        story.logger.debug(f'HTTP code {response.code}')

        return f'http code {response.code}'

    @classmethod
    async def start_container(cls, story, line):
        return await Containers.start(story, line)

    @classmethod
    def init(cls, logger):
        cls.logger = logger

    @classmethod
    def log_internal(cls):
        for key in cls.internal_services:
            commands = []
            for command in cls.internal_services[key].commands:
                commands.append(command)

            cls.logger.log_raw(
                'info', f'Discovered internal service {key} - {commands}')
