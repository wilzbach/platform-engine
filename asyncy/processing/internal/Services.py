# -*- coding: utf-8 -*-
from collections import namedtuple

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
        command = story.resolve_command(line)
        resolved_args = {}

        if service[command].arguments:
            # TODO resolve all the arguments from the story
            # TODO and construct resolved_args.
            pass

        return await service[command].handler(story=story, line=line,
                                              resolved_args=resolved_args)

    @classmethod
    def init(cls, logger):
        cls.logger = logger

    @classmethod
    def log_registry(cls):
        for key in cls.services:
            for command in cls.services[key].commands:
                cls.logger.log_raw(
                    'info', f'Discovered internal service {key}/{command}')
