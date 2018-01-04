# -*- coding: utf-8 -*-
import docker

from evenflow.Containers import Containers

from pytest import fixture


@fixture
def container():
    return Containers('hello-world')


@fixture
def docker_mock(mocker):
    mocker.patch.object(docker, 'from_env')


def test_container(container):
    assert container.name == 'hello-world'


def test_docker_run(docker_mock, container):
    container.run()
    docker.from_env().containers.run.assert_called_with(command=None)
    assert container.result == docker.from_env().containers.run()


def test_docker_run_command(docker_mock, container):
    container.run('command')
    docker.from_env().containers.run.assert_called_with(command='command')
    assert container.result == docker.from_env().containers.run()
