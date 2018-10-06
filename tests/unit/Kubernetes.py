# -*- coding: utf-8 -*-
from unittest import mock
from unittest.mock import MagicMock

from asyncy.Exceptions import K8sError
from asyncy.Kubernetes import Kubernetes

import pytest
from pytest import fixture, mark


@fixture
def line():
    return MagicMock()


def test_find_all_ports():
    services = {
        'alpine': {
            'http': {
                'port': 8080
            }
        },
        'alpha': {
            'http': {
                'port': 9092,
                'subscribe': {
                    'port': 9090
                },
                'unsubscribe': {
                    'port': 9091
                }
            }
        },
        'nested': {
            'a': {
                'b': {
                    'c': {
                        'd': {
                            'e': {
                                'http': {
                                    'subscribe': {
                                        'port': 1234
                                    },
                                    'unsubscribe': {
                                        'port': 1235
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    assert Kubernetes.find_all_ports(services['alpine']) == {8080}
    assert Kubernetes.find_all_ports(services['alpha']) == {9090, 9091, 9092}
    assert Kubernetes.find_all_ports(services['nested']) == {1234, 1235}


def test_raise_if_not_2xx(story, line):
    res = MagicMock()
    res.code = 401
    with pytest.raises(K8sError):
        Kubernetes.raise_if_not_2xx(res, story, line)

    res.code = 200
    assert Kubernetes.raise_if_not_2xx(res, story, line) is None


@mark.asyncio
async def test_create_namespace_if_required_existing(patch, story,
                                                     line, async_mock):
    res = MagicMock()
    res.code = 200
    patch.object(Kubernetes, 'make_k8s_call', new=async_mock(return_value=res))

    story.app.app_id = 'my_app'
    await Kubernetes.create_namespace_if_required(story, line)

    Kubernetes.make_k8s_call.mock.assert_called_once()
    Kubernetes.make_k8s_call.mock.assert_called_with(
        story.app, '/api/v1/namespaces/my_app')


@mark.asyncio
async def test_create_namespace_if_required(patch, story,
                                            line, async_mock):
    res_check = MagicMock()
    res_check.code = 400

    res_create = MagicMock()
    res_create.code = 200

    story.app.app_id = 'my_app'

    patch.object(Kubernetes, 'make_k8s_call',
                 new=async_mock(side_effect=[res_check, res_create]))
    patch.object(Kubernetes, 'raise_if_not_2xx')
    await Kubernetes.create_namespace_if_required(story, line)

    expected_payload = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'my_app'
        }
    }

    assert Kubernetes.make_k8s_call.mock.mock_calls == [
        mock.call(story.app, '/api/v1/namespaces/my_app'),
        mock.call(story.app, '/api/v1/namespaces', payload=expected_payload)
    ]

    assert Kubernetes.raise_if_not_2xx.called_with(res_create, story, line)


def test_is_2xx():
    res = MagicMock()
    res.code = 200
    assert Kubernetes.is_2xx(res) is True
    res.code = 210
    assert Kubernetes.is_2xx(res) is True
    res.code = 300
    assert Kubernetes.is_2xx(res) is False
    res.code = 400
    assert Kubernetes.is_2xx(res) is False
