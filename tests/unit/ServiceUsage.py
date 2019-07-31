import asyncio
import json
import urllib.parse
from unittest import mock

from pytest import approx, mark

from storyruntime.Kubernetes import Kubernetes
from storyruntime.Service import Service
from storyruntime.ServiceUsage import ServiceUsage
from storyruntime.db.Database import Database


@mark.parametrize('value', [{
    'input': '1024',
    'output': (1024.0, None),
    'suffix_len': 1
}, {
    'input': '1024m',
    'output': (1024.0, 'm'),
    'suffix_len': 1
}, {
    'input': '1024Ki',
    'output': (1024, 'Ki'),
    'suffix_len': 2
}])
def test_split_value(value):
    assert ServiceUsage.split_value(value['input'],
                                    value['suffix_len']) == value['output']


@mark.parametrize('value', [{
    'input': '21Ki',
    'split': (21.0, 'Ki'),
    'output': 21504.0
}, {
    'input': '1Mi',
    'split': (1.0, 'Mi'),
    'output': 1048576.0
}, {
    'input': '1024',
    'split': (1024.0, None),
    'output': 1024.0
}])
def test_memory_bytes(patch, value):
    patch.object(ServiceUsage, 'split_value', return_value=value['split'])
    assert ServiceUsage.memory_bytes(value['input']) == value['output']
    ServiceUsage.split_value.assert_called_with(value['input'], 2)


@mark.parametrize('value', [{
    'input': '4m',
    'split': (4.0, 'm'),
    'output': 0.004
}, {
    'input': '1k',
    'split': (1.0, 'k'),
    'output': 1000
}, {
    'input': '5',
    'split': (5.0, None),
    'output': 5.0
}])
def test_cpu_units(patch, value):
    patch.object(ServiceUsage, 'split_value', return_value=value['split'])
    assert ServiceUsage.cpu_units(value['input']) == value['output']
    ServiceUsage.split_value.assert_called_with(value['input'], 1)


@mark.parametrize('metrics', [{
    'service_tag_uuid': '08605d2c-9305-474a-949b-d57a6f01c62c',
    'memory_bytes': 12345,
    'cpu_units': 0.05,
}])
@mark.asyncio
async def test_start_metrics_recorder(patch, async_mock, app, metrics):

    # mocking
    Service.shutting_down = False

    def side_effect(*args, **kwargs):
        Service.shutting_down = True

    patch.object(
        ServiceUsage,
        'get_service_tag_uuids',
        new=async_mock(return_value=[metrics['service_tag_uuid']])
    )
    patch.object(
        ServiceUsage,
        'get_metrics',
        new=async_mock(return_value=metrics)
    )
    patch.object(
        Database,
        'create_service_usage',
        new=async_mock()
    )
    patch.object(
        Database,
        'update_service_usage',
        new=async_mock()
    )
    patch.object(
        asyncio,
        'sleep',
        new=async_mock(side_effect=side_effect)
    )

    # execution
    await ServiceUsage.start_metrics_recorder(app.config, app.logger)

    # assertion
    assert ServiceUsage.get_metrics.mock.mock_calls == [
        mock.call(metrics['service_tag_uuid'], app.config, app.logger)
    ]
    assert Database.create_service_usage.mock.mock_calls == [
        mock.call(app.config, [metrics])
    ]
    assert Database.update_service_usage.mock.mock_calls == [
        mock.call(app.config, [metrics])
    ]


@mark.parametrize('data', [{
    'service_tag_uuid': '08605d2c-9305-474a-949b-d57a6f01c62c',
    'k8s_response': {
        'items': []
    },
    'metrics': None
}, {
    'service_tag_uuid': '08605d2c-9305-474a-949b-d57a6f01c62c',
    'k8s_response': {
        'items': [{
            'containers': [{
                'usage': {
                    'cpu': '4m', 'memory': '21560Ki'
                }
            }]
        }, {
            'containers': [{
                'usage': {
                    'cpu': '14m', 'memory': '37040Ki'
                }
            }]
        }],
    },
    'metrics': {
        'cpu_units': approx(0.0135),
        'memory_bytes': approx(37136384.0),
        'service_tag_uuid': '08605d2c-9305-474a-949b-d57a6f01c62c',
    }
}])
@mark.asyncio
async def test_get_metrics(patch, async_mock, app, data):
    # prep
    res = mock.MagicMock()
    res.body = json.dumps(data['k8s_response'])
    res.code = 200

    expected_qs = urllib.parse.urlencode({
        'labelSelector': f'service-tag-uuid={data["service_tag_uuid"]}'
    })
    expected_path = Kubernetes._get_api_path_prefix('metrics') + \
        f'/pods?{expected_qs}'

    # mocking
    patch.object(Kubernetes, 'make_k8s_call', new=async_mock(return_value=res))

    # execution
    ret = await ServiceUsage.get_metrics(data['service_tag_uuid'],
                                         app.config, app.logger)

    # assertion
    assert ret == data['metrics']

    Kubernetes.make_k8s_call.mock.assert_called_with(
        app.config, app.logger, expected_path
    )
