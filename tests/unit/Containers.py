# -*- coding: utf-8 -*-
import hashlib
from unittest.mock import MagicMock

from asyncy.Exceptions import K8sError
import pytest

from asyncy.Containers import Containers
from asyncy.Kubernetes import Kubernetes
from asyncy.constants.LineConstants import LineConstants
from asyncy.constants.ServiceConstants import ServiceConstants
from asyncy.processing import Story

from pytest import fixture, mark


@fixture
def line():
    return MagicMock()


def test_is_service_reusable(story):
    story.app.services = {
        'alpine': {
            'configuration': {
                'commands': {
                    'echo': {
                        'run': 'foo'
                    }
                }
            }
        }
    }

    line = {
        LineConstants.service: 'alpine',
        LineConstants.command: 'echo'
    }

    assert Containers.is_service_reusable(story, line) is False
    story.app.services['alpine']['configuration']['commands']['echo'][
        'run'] = None

    assert Containers.is_service_reusable(story, line) is True


@mark.parametrize('reusable', [False, True])
def test_get_container_name(patch, story, line, reusable):
    patch.object(Containers, 'is_service_reusable', return_value=reusable)
    story.app.app_id = 'my_app'
    ret = Containers.get_container_name(story, line, 'alpine')
    if reusable:
        assert ret == 'asyncy--my_app-alpine-1'
    else:
        h = Containers.hash_story_line(story, line)
        assert ret == f'asyncy--{story.app.app_id}-{h}-1'


@mark.asyncio
async def test_exec():
    with pytest.raises(K8sError):
        await Containers.exec(None, None, None, None, None)


@mark.asyncio
async def test_container_get_hostname(patch, story, line):
    story.app.app_id = 'my_app'
    patch.object(Containers, 'get_container_name', return_value='foo')
    ret = await Containers.get_hostname(story, line, 'foo')
    assert ret == 'foo.my_app.svc.cluster.local'


@mark.asyncio
async def test_clean_app(patch, async_mock):
    patch.object(Kubernetes, 'clean_namespace', new=async_mock())
    app = MagicMock()
    await Containers.clean_app(app)
    Kubernetes.clean_namespace.mock.assert_called_with(app)


@mark.asyncio
async def test_remove_volume(patch, story, line, async_mock):
    patch.object(Kubernetes, 'remove_volume', new=async_mock())
    await Containers.remove_volume(story, line, 'foo')
    Kubernetes.remove_volume.mock.assert_called_with(story, line, 'foo')


@mark.asyncio
async def test_prepare_for_deployment(patch, async_mock):
    patch.object(Kubernetes, 'clean_namespace', new=async_mock())
    story = MagicMock()
    await Containers.prepare_for_deployment(story)
    Kubernetes.clean_namespace.mock.assert_called_with(story.app)


@mark.asyncio
async def test_create_volume(patch, async_mock, story, line):
    patch.object(Kubernetes, 'create_volume', new=async_mock())
    await Containers.create_volume(story, line, 'foo')
    Kubernetes.create_volume.mock.assert_called_with(story, line, 'foo')


def test_format_command(logger, app, echo_service, echo_line):
    story = Story.story(app, logger, 'echo.story')
    app.services = echo_service

    cmd = Containers.format_command(story, echo_line, 'alpine', 'echo')
    assert ['echo', '{"msg":"foo"}'] == cmd


def test_format_volume_name(patch, story, line):
    patch.object(Containers, 'is_service_reusable', return_value=True)
    assert Containers.format_volume_name(story, line, 'asyncy--alpine-1') == \
        'asyncy--alpine-1'


def test_format_volume_name_not_reusable(patch, story, line):
    patch.object(Containers, 'is_service_reusable', return_value=False)
    patch.object(Containers, 'hash_story_line', return_value='hash')
    assert Containers.format_volume_name(story, line, 'asyncy--alpine-1') == \
        'asyncy--alpine-1-hash'


def test_hash_story_line(patch, story):
    patch.object(hashlib, 'sha1')
    story.name = 'story_name'
    ret = Containers.hash_story_line(story, {'ln': '1'})

    hashlib.sha1.assert_called_with('story_name-1'.encode('utf-8'))
    assert ret == hashlib.sha1().hexdigest()


@mark.asyncio
async def test_start_no_command(patch, story, async_mock):
    line = {
        LineConstants.service: 'alpine',
        LineConstants.command: 'echo'
    }

    patch.object(Kubernetes, 'create_pod', new=async_mock())

    story.app.services = {
        'alpine': {
            ServiceConstants.config: {
                'commands': {
                    'echo': {
                    }
                }
            }
        }
    }

    patch.object(Containers, 'get_container_name',
                 return_value='asyncy-alpine')

    await Containers.start(story, line)
    Kubernetes.create_pod.mock.assert_called_with(
        story, line, 'alpine', 'asyncy-alpine',
        ['tail', '-f', '/dev/null'], None, {})


def test_format_command_no_format(logger, app, echo_service, echo_line):
    story = Story.story(app, logger, 'echo.story')
    app.services = echo_service

    config = app.services['alpine'][ServiceConstants.config]
    config['commands']['echo']['format'] = None

    cmd = Containers.format_command(story, echo_line, 'alpine', 'echo')
    assert ['echo', '{"msg":"foo"}'] == cmd
