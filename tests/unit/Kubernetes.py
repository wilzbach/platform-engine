# -*- coding: utf-8 -*-
import asyncio
import json
import ssl
from unittest import mock
from unittest.mock import MagicMock

from asyncy.entities.Volume import Volume

from asyncy.Exceptions import K8sError
from asyncy.Kubernetes import Kubernetes
from asyncy.constants.LineConstants import LineConstants
from asyncy.utils.HttpUtils import HttpUtils

import pytest
from pytest import fixture, mark

from tornado.httpclient import AsyncHTTPClient


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
async def test_create_namespace_if_required_existing(patch, app,
                                                     async_mock):
    res = MagicMock()
    res.code = 200
    patch.object(Kubernetes, 'make_k8s_call', new=async_mock(return_value=res))

    app.app_id = 'my_app'
    await Kubernetes.create_namespace(app)

    Kubernetes.make_k8s_call.mock.assert_called_once()
    Kubernetes.make_k8s_call.mock.assert_called_with(
        app, '/api/v1/namespaces/my_app')


@mark.asyncio
@mark.parametrize('create_result', [200, 500])
async def test_create_namespace_if_required(patch, app,
                                            line, async_mock, create_result):
    res_check = MagicMock()
    res_check.code = 400

    res_create = MagicMock()
    res_create.code = create_result

    app.app_id = 'my_app'

    patch.object(Kubernetes, 'make_k8s_call',
                 new=async_mock(side_effect=[res_check, res_create]))
    if create_result != 200:
        with pytest.raises(K8sError):
            await Kubernetes.create_namespace(app)
        return
    else:
        await Kubernetes.create_namespace(app)

    expected_payload = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'my_app'
        }
    }

    assert Kubernetes.make_k8s_call.mock.mock_calls == [
        mock.call(app, '/api/v1/namespaces/my_app'),
        mock.call(app, '/api/v1/namespaces', payload=expected_payload)
    ]


def test_get_hostname(story, line):
    story.app.app_id = 'my_app'
    container_name = 'alpine'
    ret = Kubernetes.get_hostname(story, line, container_name)
    assert ret == 'alpine.my_app.svc.cluster.local'


def _create_response(code: int, body: dict = None):
    res = MagicMock()
    res.code = code
    if body:
        res.body = json.dumps(body)
    return res


@mark.parametrize('first_res', [200, 409])
@mark.parametrize('resource', ['deployments', 'services',
                               'persistentvolumeclaims', 'unknown'])
@mark.asyncio
async def test_delete_resource(patch, story, async_mock, first_res, resource):
    story.app.app_id = 'my_app'
    api_responses = [
        _create_response(first_res),
        _create_response(200),
        _create_response(200),
        _create_response(404),
    ]
    patch.object(Kubernetes, 'make_k8s_call',
                 new=async_mock(side_effect=api_responses))
    patch.object(asyncio, 'sleep', new=async_mock())
    if resource == 'unknown':
        with pytest.raises(Exception):
            await Kubernetes._delete_resource(story.app, resource, 'foo')
        return
    else:
        await Kubernetes._delete_resource(story.app, resource, 'foo')

    prefix = Kubernetes._get_api_path_prefix(resource)

    assert Kubernetes.make_k8s_call.mock.mock_calls == [
        mock.call(story.app,
                  f'{prefix}/my_app/{resource}/foo'
                  f'?gracePeriodSeconds=0',
                  method='delete'),
        mock.call(story.app, f'{prefix}/my_app/{resource}/foo'),
        mock.call(story.app, f'{prefix}/my_app/{resource}/foo'),
        mock.call(story.app, f'{prefix}/my_app/{resource}/foo'),
    ]


@mark.asyncio
async def test_make_k8s_call(patch, story, async_mock):
    patch.object(HttpUtils, 'fetch_with_retry', new=async_mock())

    context = MagicMock()
    patch.object(Kubernetes, 'new_ssl_context', return_value=context)
    context.load_verify_locations = MagicMock()

    patch.init(AsyncHTTPClient)

    client = AsyncHTTPClient()

    story.app.config.CLUSTER_CERT = 'this_is\\nmy_cert'  # Notice the \\n.
    story.app.config.CLUSTER_AUTH_TOKEN = 'my_token'
    story.app.config.CLUSTER_HOST = 'k8s.local'

    path = '/hello_world'

    payload = {
        'foo': 'bar'
    }

    expected_kwargs = {
        'ssl_options': context,
        'headers': {
            'Authorization': 'bearer my_token',
            'Content-Type': 'application/json; charset=utf-8'
        },
        'method': 'POST',
        'body': json.dumps(payload)
    }

    assert await Kubernetes.make_k8s_call(story.app, path, payload) \
        == HttpUtils.fetch_with_retry.mock.return_value

    HttpUtils.fetch_with_retry.mock.assert_called_with(
        3, story.app.logger, 'https://k8s.local/hello_world', client,
        expected_kwargs)

    # Notice the \n. \\n MUST be converted to \n in Kubernetes#make_k8s_call.
    context.load_verify_locations.assert_called_with(cadata='this_is\nmy_cert')


def test_new_ssl_context():
    assert isinstance(Kubernetes.new_ssl_context(), ssl.SSLContext)


@mark.parametrize('res_code', [200, 400])
@mark.asyncio
async def test_create_pod(patch, async_mock, story, line, res_code):
    res = MagicMock()
    res.code = res_code
    patch.object(Kubernetes, 'create_deployment', new=async_mock())
    patch.object(Kubernetes, 'create_service', new=async_mock())
    patch.object(Kubernetes, 'make_k8s_call', new=async_mock(return_value=res))

    image = 'alpine/alpine:latest'
    start_command = ['/bin/sleep', '1d']
    container_name = 'asyncy--alpine-1'
    env = {'token': 'foo'}

    story.app.app_id = 'my_app'

    await Kubernetes.create_pod(
        story, line, image, container_name, start_command, None, env, [])

    Kubernetes.make_k8s_call.mock.assert_called_with(
        story.app,
        '/apis/apps/v1/namespaces/my_app/deployments/asyncy--alpine-1')

    if res_code == 200:
        assert Kubernetes.create_deployment.mock.called is False
        assert Kubernetes.create_service.mock.called is False
    else:
        Kubernetes.create_deployment.mock.assert_called_with(
            story, line, image, container_name, start_command, None, env, [])
        Kubernetes.create_service.mock.assert_called_with(
            story, line, container_name)


@mark.asyncio
async def test_create_deployment(patch, async_mock, story):
    container_name = 'asyncy--alpine-1'
    story.app.app_id = 'my_app'
    image = 'alpine:latest'

    env = {'token': 'asyncy-19920', 'username': 'asyncy'}
    start_command = ['/bin/bash', 'sleep', '10000']
    shutdown_command = ['wall', 'Shutdown']

    volumes = [Volume(persist=False, name='tmp', mount_path='/tmp'),
               Volume(persist=True, name='db', mount_path='/db')]

    patch.object(Kubernetes, 'remove_volume', new=async_mock())
    patch.object(Kubernetes, 'create_volume', new=async_mock())

    expected_payload = {
        'apiVersion': 'apps/v1',
        'kind': 'Deployment',
        'metadata': {
            'name': container_name,
            'namespace': story.app.app_id
        },
        'spec': {
            'replicas': 1,
            'strategy': {
                'type': 'RollingUpdate'
            },
            'selector': {
                'matchLabels': {
                    'app': container_name
                }
            },
            'template': {
                'metadata': {
                    'labels': {
                        'app': container_name
                    }
                },
                'spec': {
                    'containers': [
                        {
                            'name': container_name,
                            'image': image,
                            'command': start_command,
                            'imagePullPolicy': 'Always',
                            'env': [{'name': 'token', 'value': 'asyncy-19920'},
                                    {'name': 'username', 'value': 'asyncy'}],
                            'lifecycle': {
                                'preStop': {
                                    'exec': {
                                        'command': shutdown_command
                                    }
                                }
                            },
                            'volumeMounts': [
                                {
                                    'mountPath': volumes[0].mount_path,
                                    'name': volumes[0].name
                                },
                                {
                                    'mountPath': volumes[1].mount_path,
                                    'name': volumes[1].name
                                }
                            ]
                        }
                    ],
                    'volumes': [
                        {
                            'name': volumes[0].name,
                            'persistentVolumeClaim': {
                                'claimName': volumes[0].name
                            }
                        },
                        {
                            'name': volumes[1].name,
                            'persistentVolumeClaim': {
                                'claimName': volumes[1].name
                            }
                        }
                    ]
                }
            }
        }
    }

    patch.object(asyncio, 'sleep', new=async_mock())

    expected_create_path = f'/apis/apps/v1/namespaces/' \
                           f'{story.app.app_id}/deployments'
    expected_verify_path = f'/apis/apps/v1/namespaces/{story.app.app_id}' \
                           f'/deployments/{container_name}'

    patch.object(Kubernetes, 'make_k8s_call', new=async_mock(side_effect=[
        _create_response(404),
        _create_response(201),
        _create_response(200, {'status': {'readyReplicas': 0}}),
        _create_response(200, {'status': {'readyReplicas': 0}}),
        _create_response(200, {'status': {'readyReplicas': 1}})
    ]))
    line = {}

    await Kubernetes.create_deployment(story, line, image, container_name,
                                       start_command, shutdown_command, env,
                                       volumes)

    Kubernetes.remove_volume.mock.assert_called_once()
    Kubernetes.remove_volume.mock.assert_called_with(
        story, line, volumes[0].name)

    assert Kubernetes.create_volume.mock.mock_calls == [
        mock.call(story, line, volumes[0].name, volumes[0].persist),
        mock.call(story, line, volumes[1].name, volumes[1].persist)
    ]

    assert Kubernetes.make_k8s_call.mock.mock_calls == [
        mock.call(story.app, expected_create_path, expected_payload),
        mock.call(story.app, expected_create_path, expected_payload),
        mock.call(story.app, expected_verify_path),
        mock.call(story.app, expected_verify_path),
        mock.call(story.app, expected_verify_path)
    ]


@mark.asyncio
async def test_create_service(patch, story, async_mock):
    container_name = 'asyncy--alpine-1'
    line = {
        LineConstants.service: 'alpine'
    }
    patch.object(Kubernetes, 'find_all_ports', return_value={10, 20, 30})
    patch.object(Kubernetes, 'raise_if_not_2xx')
    patch.object(Kubernetes, 'make_k8s_call', new=async_mock())
    patch.object(asyncio, 'sleep', new=async_mock())
    story.app.app_id = 'my_app'

    expected_payload = {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {
            'name': container_name,
            'namespace': story.app.app_id,
            'labels': {
                'app': container_name
            }
        },
        'spec': {
            'ports': [
                {'port': 10, 'protocol': 'TCP', 'targetPort': 10},
                {'port': 20, 'protocol': 'TCP', 'targetPort': 20},
                {'port': 30, 'protocol': 'TCP', 'targetPort': 30}
            ],
            'selector': {
                'app': container_name
            }
        }
    }

    expected_path = f'/api/v1/namespaces/{story.app.app_id}/services'
    await Kubernetes.create_service(story, line, container_name)
    Kubernetes.make_k8s_call.mock.assert_called_with(
        story.app, expected_path, expected_payload)

    Kubernetes.raise_if_not_2xx.assert_called_with(
        Kubernetes.make_k8s_call.mock.return_value, story, line)
    asyncio.sleep.mock.assert_called()


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
