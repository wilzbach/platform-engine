# -*- coding: utf-8 -*-
import hashlib

import ujson

from .Exceptions import ContainerSpecNotRegisteredError, K8sError
from .Kubernetes import Kubernetes
from .Types import StreamingService
from .constants.LineConstants import LineConstants
from .constants.ServiceConstants import ServiceConstants
from .utils import Dict


class Containers:

    @classmethod
    def format_volume_name(cls, story, line, name):
        """
        Returns a derived volume name from the story and line if
        the container in question cannot be reused. Otherwise, this returns
        the same name passed in as is.
        """
        if not cls.is_service_reusable(story, line):
            name = f'{name}-{cls.hash_story_line(story, line)}'

        return name

    @classmethod
    async def remove_volume(cls, story, line, name):
        await Kubernetes.remove_volume(story, line, name)

    @classmethod
    async def prepare_for_deployment(cls, story):
        await Kubernetes.clean_namespace(story.app)

    @classmethod
    async def create_volume(cls, story, line, name):
        await Kubernetes.create_volume(story, line, name)

    @classmethod
    async def create_and_start(cls, story, line, service, container_name):
        # Note: 'image' is inserted by asyncy.Apps, and is not a part of the
        # OMG spec.
        omg = story.app.services[service][ServiceConstants.config]
        image = omg.get('image', service)

        command_conf = Dict.find(omg, f'commands.'
                                      f'{line[LineConstants.command]}')

        shutdown_command = Dict.find(omg, f'lifecycle.shutdown.command')

        if command_conf.get('run'):
            start_command = Dict.find(command_conf, 'run.command')
        else:
            start_command = Dict.find(omg, f'lifecycle.startup.command')

        if start_command is None:
            start_command = ['tail', '-f', '/dev/null']

        # targets = {}
        # binds = []

        # if omg.get('volumes'):
        #     for name, data in omg['volumes'].items():
        #         vol_name = f'asyncy--{service}-{name}'
        #         vol_name = cls.format_volume_name(story, line, vol_name)
        #         if not data.get('persist'):
        #             await cls.remove_volume(story, line, vol_name)
        #         await cls.create_volume(story, line, vol_name)
        #         binds.append(f'{name}:{data["target"]}')
        #         targets[data['target']] = {}

        env = {}
        for key, val in story.app.environment.items():
            if isinstance(val, dict):
                if key == service:
                    for k, v in val.items():
                        env[k] = v
                continue

            env[key] = val

        await Kubernetes.create_pod(story, line, image, container_name,
                                    start_command, shutdown_command, env)

    @classmethod
    async def clean_app(cls, app):
        await Kubernetes.clean_namespace(app)

    @classmethod
    def is_service_reusable(cls, story, line):
        """
        A service is reusable when it doesn't need to execute a lifecycle
        command. If there's a run section in the command's config, then
        cannot be reused. Reusable commands do not have a run in their config,
        and are started via the global lifecycle config.
        """
        service = line[LineConstants.service]
        command = line[LineConstants.command]

        run = Dict.find(story.app.services,
                        f'{service}.configuration.commands.{command}.run')

        return run is None

    @classmethod
    async def get_hostname(cls, story, line, service_alias):
        container = cls.get_container_name(story, line, service_alias)
        return Kubernetes.get_hostname(story, line, container)

    @classmethod
    async def start(cls, story, line):
        """
        Creates and starts a container as declared by line['service'].

        If a container already exists, then it will be reused.
        """
        service = line[LineConstants.service]
        story.logger.info(f'Starting container {service}')
        container_name = cls.get_container_name(story, line, service)
        await cls.create_and_start(story, line, service, container_name)
        hostname = await cls.get_hostname(story, line, service)

        ss = StreamingService(name=service, command=line['command'],
                              container_name=container_name,
                              hostname=hostname)

        story.logger.info(f'Started container {container_name}: {ss}')
        return ss

    @classmethod
    def format_command(cls, story, line, container_name, command):
        services = story.app.services or {}
        spec = services.get(container_name)

        if spec is None:
            raise ContainerSpecNotRegisteredError(
                container_name=container_name
            )

        args = spec[ServiceConstants.config]['commands'][command]\
            .get('arguments')

        if args is None:
            return [command]

        command_format = spec[ServiceConstants.config]['commands'][command]\
            .get('format')
        if command_format is None:
            # Construct a dictionary of all arguments required and send them
            # as a JSON string to the command.
            all_args = {}
            for k in args:
                all_args[k] = story.argument_by_name(line, k)

            return [command, ujson.dumps(all_args)]

        command_parts = command_format.split(' ')

        for k in args:
            actual = story.argument_by_name(line, k)
            for i in range(0, len(command_parts)):
                command_parts[i] = command_parts[i].replace('{' + k + '}',
                                                            actual)

        return command_parts

    @classmethod
    def get_container_name(cls, story, line, name):
        """
        If a container can be reused (where reuse is defined as a command
        without a run section in it's config), it'll return a generic name
        like asyncy--app_id-foo-1, otherwise something cryptic:
        asyncy--app_id-sha1(foo)-1.

        Why a hash? Story names can have DNS reserved characters in them,
        and hence to normalise it, we need to create a hash here.
        """
        if cls.is_service_reusable(story, line):
            return f'asyncy--{story.app.app_id}-{name}-1'

        h = cls.hash_story_line(story, line)
        return f'asyncy--{story.app.app_id}-{h}-1'

    @classmethod
    def hash_story_line(cls, story, line):
        return hashlib.sha1(f'{story.name}-{line["ln"]}'
                            .encode('utf-8')).hexdigest()

    @classmethod
    async def exec(cls, logger, story, line, container_name, command):
        """
        Executes a command in the given container.

        Returns:
        Output of the process (stdout).

        Raises:
        asyncy.Exceptions.K8sError:
            If the execution failed for an unknown reason.
        """
        raise K8sError(story=story, line=line, message='Not implemented')
