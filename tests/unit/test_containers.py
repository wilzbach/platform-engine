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
    return docker.from_env()


def test_container(container):
    assert container.name == 'hello-world'


def test_docker_run(docker_mock, container):
    container.run()
    docker_mock.containers.run.assert_called_with('hello-world', command=None)
    docker_mock.images.pull.assert_called_with('hello-world')
    assert container.output == docker.from_env().containers.run()


def test_docker_run_command(docker_mock, container):
    container.run('command')
    containers = docker_mock.containers.run
    containers.assert_called_with('hello-world', command='command')


def test_containers_results(container):
    container.output = 'output'
    assert container.result() == 'output'
