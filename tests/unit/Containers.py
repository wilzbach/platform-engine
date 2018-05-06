# -*- coding: utf-8 -*-

from asyncy.Containers import Containers
from asyncy.processing import Story

from docker import DockerClient


def test_container_exec(patch, config, logger):
    patch.object(DockerClient, 'containers')
    DockerClient.containers.get.return_value.exec_run \
        .return_value = [0, 'output']
    patch.object(Story, 'story')

    story = Story.story(config, logger, None, 'story_name')
    story.get_environment.return_value = {'foo': 'bar'}

    result = Containers.exec(logger, story, 'container_name', 'command')

    DockerClient.containers.get.return_value.exec_run.assert_called_with(
        'command', environment={'foo': 'bar'}
    )
    assert DockerClient.containers.get.call_count == 1
    assert result == 'output'
