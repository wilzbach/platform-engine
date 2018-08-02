# -*- coding: utf-8 -*-
from collections import namedtuple

from ...Exceptions import AsyncyError

Command = namedtuple('Command', ['arguments', 'output_type', 'handler'])
Service = namedtuple('Service', ['commands'])


class Services:
    services = {}
    logger = None

    @classmethod
    def register(cls, name, command, arguments, output_type, handler):
        service = cls.services.get(name)
        if service is None:
            service = Service(commands={})
            cls.services[name] = service

        service.commands[command] = Command(arguments=arguments,
                                            output_type=output_type,
                                            handler=handler)

    @classmethod
    def is_internal(cls, service):
        return cls.services.get(service) is not None

    @classmethod
    async def execute(cls, story, line):
        service = cls.services[line['service']]
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
    def init(cls, logger):
        cls.logger = logger

    @classmethod
    def log_registry(cls):
        for key in cls.services:
            commands = []
            for command in cls.services[key].commands:
                commands.append(command)

            cls.logger.log_raw(
                'info', f'Discovered internal service {key} - {commands}')
