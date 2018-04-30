# -*- coding: utf-8 -*-
from unittest.mock import Mock

from asyncy.Cli import Cli
from asyncy.rpc import http_proxy_pb2
from asyncy.rpc.http_proxy_pb2_grpc import HttpProxyStub

from click.testing import CliRunner

import grpc

from pytest import fixture


@fixture
def runner():
    return CliRunner()


@fixture
def kwargs():
    return {'block': None, 'json_context': None,
            'json_environment': None, 'start': None}


@fixture
def run_story_stub(patch):
    patch.object(grpc, 'insecure_channel')
    patch.init(HttpProxyStub)
    stub = HttpProxyStub(channel=None)
    mock = Mock()
    type(stub).RunStory = mock.method()
    patch.object(HttpProxyStub, '__init__', return_value=None)
    patch.object(http_proxy_pb2.Request, '__init__', return_value=None)

    return stub


def test_cli_run(patch, runner, kwargs, run_story_stub):
    result = runner.invoke(Cli.run, ['story_name', 'app_id'])
    http_proxy_pb2.Request.__init__.assert_called_with(
        app_id='app_id', story_name='story_name', **kwargs
    )
    run_story_stub.RunStory.assert_called_once()
    assert result.exit_code == 0


def test_cli_run_host(patch, runner, kwargs, run_story_stub):
    result = runner.invoke(Cli.run, ['--host', 'myapp.com',
                                     'story_name', 'app_id'])
    grpc.insecure_channel.assert_called_with('myapp.com:32781')
    assert result.exit_code == 0


def test_cli_run_port(patch, runner, kwargs, run_story_stub):
    result = runner.invoke(Cli.run, ['--port', '1234', 'story_name', 'app_id'])
    grpc.insecure_channel.assert_called_with('localhost:1234')
    assert result.exit_code == 0


def test_cli_run_block(patch, runner, kwargs, run_story_stub):
    kwargs['block'] = 'line'
    result = runner.invoke(Cli.run, ['story', 'app_id', '--block', 'line'])

    http_proxy_pb2.Request.__init__.assert_called_with(
        app_id='app_id', story_name='story', **kwargs
    )
    assert result.exit_code == 0


def test_cli_run_start(patch, runner, kwargs, run_story_stub):
    kwargs['start'] = 'line'
    result = runner.invoke(Cli.run, ['story', 'app_id', '--start', 'line'])

    http_proxy_pb2.Request.__init__.assert_called_with(
        app_id='app_id', story_name='story', **kwargs
    )
    assert result.exit_code == 0


def test_cli_run_context(patch, runner, kwargs, run_story_stub):
    kwargs['json_context'] = '{"variable": "value"}'
    result = runner.invoke(Cli.run, ['story', 'app_id', '--context',
                                     '{"variable": "value"}'])
    http_proxy_pb2.Request.__init__.assert_called_with(
        app_id='app_id', story_name='story', **kwargs
    )
    assert result.exit_code == 0


def test_cli_run_environment(patch, runner, kwargs, run_story_stub):
    kwargs['json_environment'] = '{"variable": "value"}'
    result = runner.invoke(Cli.run, ['story', 'app_id', '--environment',
                                     '{"variable": "value"}'])
    http_proxy_pb2.Request.__init__.assert_called_with(
        app_id='app_id', story_name='story', **kwargs
    )
    assert result.exit_code == 0
