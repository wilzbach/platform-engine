# -*- coding: utf-8 -*-
import asyncio
import hashlib
import struct

from tornado.httpclient import AsyncHTTPClient, HTTPError

import ujson

from .Exceptions import AsyncyError, ContainerSpecNotRegisteredError, \
    DockerError
from .Types import StreamingService
from .constants.LineConstants import LineConstants
from .constants.ServiceConstants import ServiceConstants
from .utils import Dict
from .utils.HttpUtils import HttpUtils

MAX_RETRIES = 3

API_VERSION = 'v1.37'


class Containers:

    @classmethod
    async def get_network_name(cls, story, line):
        # We can't filter down by networks because of a bug in Docker.
        # See https://github.com/moby/moby/issues/37673.
        resp = await cls._make_docker_request(story, line, '/networks')
        if resp.code != 200:
            raise DockerError(
                story=story, line=line,
                message=f'Failed to list networks! error={resp.error}')
        network_list = ujson.loads(resp.body)

        name = None
        for network in network_list:
            if 'asyncy-backend' in network['Name']:
                if name is not None:
                    raise AsyncyError(
                        story=story, line=line,
                        message=f'There are two or more networks tagged as '
                                f'asyncy-backend. Please stop the others '
                                f'before continuing.')
                name = network['Name']

        return name

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
        await cls._make_docker_request(story, line, f'/volumes/{name}',
                                       method='DELETE')

    @classmethod
    async def create_volume(cls, story, line, name):
        data = {
            'Name': name
        }
        resp = await cls._make_docker_request(story, line, f'/volumes/create',
                                              method='POST', data=data)
        if resp.code != 201:
            raise DockerError(story=story, line=line,
                              message=f'Failed to create volume {name}')

    @classmethod
    async def _create_container(cls, story, line, service,
                                container_name, entrypoint):
        # Note: 'image' is inserted by platform-bootstrap, and NOT a part of
        # microservice.yml/omg.yml.
        omg = story.app.services[service]
        image = omg.get('image', service)
        path = f'/containers/create?name={container_name}'
        targets = {'/asyncy': {}}
        binds = ['application-volume:/asyncy']

        if omg.get('volumes'):
            for name, data in omg['volumes'].items():
                vol_name = f'asyncy--{service}-{name}'
                vol_name = cls.format_volume_name(story, line, vol_name)
                if not data.get('persist'):
                    await cls.remove_volume(story, line, vol_name)
                await cls.create_volume(story, line, vol_name)
                binds.append(f'{name}:{data["target"]}')
                targets[data['target']] = {}

        env_arr = []
        for key, val in story.app.environment.items():
            if isinstance(val, dict):
                if key == service:
                    for k, v in val.items():
                        env_arr.append(f'{k}={v}')
                continue

            env_arr.append(f'{key}={val}')

        data = {
            'AttachStdout': False,
            'AttachStderr': False,
            'Env': env_arr,
            'Image': image,
            'Volumes': targets,
            'HostConfig': {
                'Binds': binds,
                'NetworkMode': await cls.get_network_name(story, line)
            },
            'Entrypoint': entrypoint
        }

        resp = await cls._make_docker_request(story, line, path, data,
                                              method='POST')
        if resp.code == 201:
            # Wait until the container has been created completely.
            while True:
                await asyncio.sleep(.500)
                out = await cls.inspect_container(story, line, container_name)
                if out is not None:
                    break

            return

        raise DockerError(
            story=story, line=line,
            message=f'Failed to create {container_name} from {image}! '
                    f'error={resp.error}, response={resp.body}')

    @classmethod
    async def _start_container(cls, story, line, container):
        url = f'/containers/{container}/start'
        response = await cls._make_docker_request(
            story, line, url, data='', method='POST')
        if response.code == 204 or response.code == 304:
            story.logger.info(f'Started container {container}')
            return None

        raise DockerError(
            story=story, line=line,
            message=f'Failed to start {container}! error={response.error}')

    @classmethod
    async def inspect_container(cls, story, line, container):
        response = await cls._make_docker_request(
            story, line, f'/containers/{container}/json')
        if response.code == 200:
            return ujson.loads(response.body)

        return None

    @classmethod
    async def stop_container(cls, story, line, container):
        response = await cls._make_docker_request(
            story, line, f'/containers/{container}/stop')
        if response.code == 204 \
                or response.code == 304:
            story.logger.info(f'Stopped container {container}')
            return ujson.loads(response.body)

        story.logger.info(f'Failed to stop container {container}')
        raise DockerError(story=story, line=line,
                          message=f'Failed to stop container {container}')

    @classmethod
    async def remove_container(cls, story, line, container, force=False):
        response = await cls._make_docker_request(
            story, line, f'/containers/{container}?force={ujson.dumps(force)}',
            method='DELETE')
        if response.code == 204 \
                or response.code == 304 \
                or response.code == 404:
            story.logger.info(f'Removed container {container}')
            return None

        story.logger.info(f'Failed to remove container {container}')
        raise DockerError(story=story, line=line,
                          message=f'Failed to remove container {container}')

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
        c = await cls.inspect_container(story, line, container)
        return c['Config']['Hostname']  # TODO safety checks

    @classmethod
    async def start(cls, story, line):
        """
        Creates and starts a container as declared by line['service'].

        If a container already exists, then it will be reused.
        """
        service = line[LineConstants.service]
        story.logger.info(f'Starting container {service}')

        omg = story.app.services[service]
        command_conf = Dict.find(omg, f'{ServiceConstants.config}.commands.'
                                      f'{line[LineConstants.command]}')

        if command_conf.get('run'):
            command = Dict.find(command_conf, 'run.command')
        else:
            command = Dict.find(omg, f'{ServiceConstants.config}.'
                                     f'lifecycle.startup.command')

        container_name = cls.get_container_name(story, line, service)

        if command is None:
            raise AsyncyError(
                message=f'No startup/run command found for {container_name}',
                story=story, line=line)

        container = await cls.inspect_container(story, line,
                                                container_name)

        if container is None:
            await cls._create_container(story, line, service,
                                        container_name, command)
            await cls._start_container(story, line, container_name)
            container = await cls.inspect_container(story, line,
                                                    container_name)

        if container['State']['Running'] is False:
            await cls._start_container(story, line, container_name)

        ss = StreamingService(name=line['service'], command=line['command'],
                              container_name=container_name,
                              hostname=container['Config']['Hostname'])

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
        like asyncy--foo-1, otherwise something cryptic: asyncy--sha1(foo)-1.

        Why a hash? Story names can have Docker reserved characters in them,
        and hence to normalise it, we need to create a hash here.
        """
        if cls.is_service_reusable(story, line):
            return f'asyncy--{name}-1'

        h = cls.hash_story_line(story, line)
        return f'asyncy--{h}-1'

    @classmethod
    def hash_story_line(cls, story, line):
        return hashlib.sha1(f'{story.name}-{line["ln"]}'
                            .encode('utf-8')).hexdigest()

    @classmethod
    async def exec(cls, logger, story, line, container_name, command):
        """
        Executes a command asynchronously in the given container.

        Returns:
        Output of the process (stdout).

        Raises:
        asyncy.Exceptions.DockerError:
            If the execution failed for an unknown reason.
        """
        logger.log('container-start', container_name)
        container = cls.get_container_name(story, line, container_name)
        exec_create_post_data = {
            'Container': container,
            'User': 'root',
            'Privileged': False,
            'Cmd': cls.format_command(story, line, container_name, command),
            'AttachStdin': False,
            'AttachStdout': True,
            'AttachStderr': True,
            'Tty': False
        }

        logger.debug('Creating exec...')

        response = await cls._make_docker_request(
            story, line, f'/containers/{container}/exec',
            exec_create_post_data, method='POST')

        create_result = ujson.loads(response.body)
        logger.debug(f'Exec creation result {create_result}')

        exec_id = create_result['Id']
        exec_start_url = f'/exec/{exec_id}/start'
        exec_start_post_data = {
            'Tty': False,
            'Detach': False
        }

        logger.debug('Starting exec...')
        response = await cls._make_docker_request(
            story, line, exec_start_url,
            exec_start_post_data, method='POST')

        logger.debug('Exec has a response! Parsing...')

        # Read our stdin/stdout multiplexed stream.
        # https://docs.docker.com/engine/api/v1.32/#operation/ContainerAttach
        stdout = ''
        stderr = ''

        while True:
            header = response.buffer.read(8)

            if header is b'':  # EOS.
                break

            length = struct.unpack('>I', header[4:])  # Big endian.

            output = response.buffer.read(length[0]).decode('utf-8')

            if header[0] == 1:
                stdout += output
            elif header[0] == 2:
                stderr += output
            else:
                raise Exception('Don\'t know what {0} in the header means'
                                .format(header[0]))

        logger.log('container-end', container_name)

        logger.debug(f'Exec response - stdout {stdout}, stderr {stderr}')

        return stdout[:-1]  # Truncate the leading \n from the console.

    @classmethod
    async def _make_docker_request(cls, story, line, path,
                                   data=None, headers=None, method='GET'):
        endpoint = story.app.config.DOCKER_HOST

        if story.app.config.DOCKER_TLS_VERIFY == '1':
            endpoint = endpoint.replace('http://', 'https://')

        url = f'{endpoint}/{API_VERSION}{path}'

        if headers is None and data is not None:
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }

        kwargs = {
            'method': method,
            'headers': headers
        }

        if data is not None:
            kwargs['body'] = ujson.dumps(data)

        story.logger.debug(f'Dialing {method} {url} with '
                           f'headers {headers} and body {data}')

        cls._insert_auth_kwargs(story, kwargs)
        http_client = AsyncHTTPClient()

        return await cls._fetch_with_retry(story, line, url,
                                           http_client, kwargs)

    @classmethod
    async def _fetch_with_retry(cls, story, line, url, http_client, kwargs):
        try:
            return await HttpUtils.fetch_with_retry(MAX_RETRIES, story.logger,
                                                    url, http_client, kwargs)
        except HTTPError as e:
            raise DockerError(message=f'Failed to call {url}!',
                              story=story, line=line)

    @classmethod
    def _insert_auth_kwargs(cls, story, kwargs):
        if story.app.config.DOCKER_TLS_VERIFY != '':
            kwargs['validate_cert'] = True
            cert_path = story.app.config.DOCKER_CERT_PATH
            kwargs['ca_certs'] = cert_path + '/ca.pem'
            kwargs['client_key'] = cert_path + '/key.pem'
            kwargs['client_cert'] = cert_path + '/cert.pem'
