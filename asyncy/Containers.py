# -*- coding: utf-8 -*-
import struct

from tornado.httpclient import AsyncHTTPClient, HTTPError

import ujson

from .Exceptions import ContainerSpecNotRegisteredError, DockerError

MAX_RETRIES = 3

API_VERSION = 'v1.37'


class Containers:

    @classmethod
    def format_command(cls, story, line, container_name, command):
        services = story.app.services.get('services', {})
        spec = services.get(container_name)

        if spec is None:
            raise ContainerSpecNotRegisteredError(
                container_name=container_name
            )

        args = spec['config']['commands'][command].get('arguments')

        if args is None:
            return [command]

        command_format = spec['config']['commands'][command].get('format')
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
        http_client = AsyncHTTPClient()

        container = f'asyncy--{container_name}-1'

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

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        endpoint = story.app.config.DOCKER_HOST

        if story.app.config.DOCKER_TLS_VERIFY == '1':
            endpoint = endpoint.replace('http://', 'https://')

        exec_create_url = f'{endpoint}/{API_VERSION}' \
                          f'/containers/{container}/exec'

        create_kwargs = {
            'method': 'POST',
            'headers': headers,
            'body': ujson.dumps(exec_create_post_data)
        }

        cls._insert_auth_kwargs(story, create_kwargs)

        response = await cls._fetch_with_retry(story, line, exec_create_url,
                                               http_client, create_kwargs)

        create_result = ujson.loads(response.body)

        exec_id = create_result['Id']

        exec_start_url = f'{endpoint}/{API_VERSION}/exec/{exec_id}/start'

        exec_start_post_data = {
            'Tty': False,
            'Detach': False
        }

        exec_start_kwargs = {
            'method': 'POST',
            'headers': headers,
            'body': ujson.dumps(exec_start_post_data)
        }

        cls._insert_auth_kwargs(story, exec_start_kwargs)

        response = await cls._fetch_with_retry(story, line, exec_start_url,
                                               http_client, exec_start_kwargs)

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

        return stdout[:-1]  # Truncate the leading \n from the console.

    @classmethod
    async def _fetch_with_retry(cls, story, line, url, http_client, kwargs):
        attempts = 0
        while attempts < MAX_RETRIES:
            attempts = attempts + 1
            try:
                return await http_client.fetch(url, **kwargs)
            except HTTPError as e:
                story.logger.log_raw(
                    'error',
                    f'Failed to call {url}; attempt={attempts}; err={str(e)}'
                )

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
