# -*- coding: utf-8 -*-
from io import BytesIO
from unittest.mock import MagicMock

from asyncy.Config import Config
from asyncy.Containers import Containers, MAX_RETRIES
from asyncy.Exceptions import DockerError

import pytest
from pytest import mark

from tornado.httpclient import AsyncHTTPClient, HTTPError


@mark.asyncio
async def test_container_exec(patch, story, app, logger, async_mock):
    create_response = MagicMock()
    create_response.body = '{"Id": "exec_id"}'

    exec_response = MagicMock()
    exec_response.buffer = BytesIO(b'\x01\x00\x00\x00\x00\x00\x00\x03asy'
                                   b'\x01\x00\x00\x00\x00\x00\x00\x01n'
                                   b'\x01\x00\x00\x00\x00\x00\x00\x01c'
                                   b'\x01\x00\x00\x00\x00\x00\x00\x02y\n')

    patch.object(AsyncHTTPClient, '__init__', return_value=None)

    patch.object(AsyncHTTPClient, 'fetch',
                 new=async_mock(side_effect=[create_response, exec_response]))

    app.config = Config()

    story.app = app
    story.prepare()

    result = await Containers.exec(logger, story, 'alpine', 'pwd')

    assert result == 'asyncy'

    fetch = AsyncHTTPClient.fetch.mock

    endpoint = app.config.DOCKER_HOST
    if story.app.config.DOCKER_TLS_VERIFY == '1':
        endpoint = endpoint.replace('http://', 'https://')

    assert fetch.mock_calls[0][1][1] == \
        '{0}/v1.37/containers/alpine/exec'.format(endpoint)
    assert fetch.mock_calls[0][2]['method'] == 'POST'
    assert fetch.mock_calls[0][2]['body'] == \
        '{"Container":"alpine","User":"root","Privileged":false,' \
        '"Cmd":["pwd"],"AttachStdin":false,' \
        '"AttachStdout":true,"AttachStderr":true,"Tty":false}'

    assert fetch.mock_calls[1][1][1] == \
        '{0}/v1.37/exec/exec_id/start'.format(endpoint)
    assert fetch.mock_calls[1][2]['method'] == 'POST'
    assert fetch.mock_calls[1][2]['body'] == '{"Tty":false,"Detach":false}'


@mark.asyncio
async def test_fetch_with_retry(patch, story):
    def raise_error(url):
        raise HTTPError(500)

    patch.object(AsyncHTTPClient, 'fetch', side_effect=raise_error)
    client = AsyncHTTPClient()

    with pytest.raises(DockerError):
        # noinspection PyProtectedMember
        await Containers._fetch_with_retry(story, 'url', client, {})

    assert client.fetch.call_count == MAX_RETRIES
