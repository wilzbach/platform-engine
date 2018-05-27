# -*- coding: utf-8 -*-
import struct

from tornado.httpclient import AsyncHTTPClient

import ujson


MAX_RETRIES = 3

API_VERSION = 'v1.37'


class Containers:

    @classmethod
    async def exec(cls, logger, story, name, command):
        """
        Executes a command asynchronously in the given container.

        Returns:
        Output of the process (stdout).

        Raises:
        asyncy.Exceptions.DockerError:
            If the execution failed for an unknown reason.
        """

        # TODO 27/05/2018: retry logic

        logger.log('container-start', name)
        http_client = AsyncHTTPClient()

        env_arr = []
        for key in story.environment:
            env_arr.append(key + '=' + story.environment[key])

        exec_create_post_data = {
            'Container': name,
            'User': 'root',
            'Privileged': False,
            'Env': env_arr,
            'Cmd': [command],
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

        exec_create_url = '{0}/{1}/containers/{2}/exec'\
            .format(endpoint, API_VERSION, name)

        create_kwargs = {
            'method': 'POST',
            'headers': headers,
            'body': ujson.dumps(exec_create_post_data)
        }

        cls._insert_auth_kwargs(story, create_kwargs)

        response = await http_client.fetch(exec_create_url, **create_kwargs)

        create_result = ujson.loads(response.body)

        exec_id = create_result['Id']

        exec_start_url = '{0}/{1}/exec/{2}/start'\
            .format(endpoint, API_VERSION, exec_id)

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

        response = await http_client.fetch(
            exec_start_url,
            **exec_start_kwargs)

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

        logger.log('container-end', name)

        return stdout[:-1]  # Truncate the leading \n from the console.

    @classmethod
    def _insert_auth_kwargs(cls, story, kwargs):
        if story.app.config.DOCKER_TLS_VERIFY != '':
            kwargs['validate_cert'] = True
            cert_path = story.app.config.DOCKER_CERT_PATH
            kwargs['ca_certs'] = cert_path + '/ca.pem'
            kwargs['client_key'] = cert_path + '/key.pem'
            kwargs['client_cert'] = cert_path + '/cert.pem'
