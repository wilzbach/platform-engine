# -*- coding: utf-8 -*-
import time

from asyncy.Service import Service
from asyncy.rpc import http_proxy_pb2_grpc

from click.testing import CliRunner

import grpc

from pytest import fixture


@fixture
def runner():
    return CliRunner()


@fixture
def kwargs():
    return {'block': None, 'context': None, 'environment': None, 'start': None}


def sleep():
    raise OSError


def test_server(patch, runner):
    patch.object(grpc, 'server')

    patch.object(time, 'sleep', side_effect=KeyboardInterrupt)
    patch.object(http_proxy_pb2_grpc, 'add_HttpProxyServicer_to_server')

    result = runner.invoke(Service.start)
    grpc.server.assert_called_once()
    assert result.exit_code == 0
