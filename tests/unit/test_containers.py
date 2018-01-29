# -*- coding: utf-8 -*-
from asyncy.Containers import Containers

import docker

from pytest import fixture


@fixture
def container():
    return Containers('hello-world')


@fixture
def docker_mock(mocker):
    mocker.patch.object(docker, 'from_env')
    return docker.from_env()


def test_containers(container):
    assert container.name == 'hello-world'


def test_containers_aliases(container):
    assert container.aliases['node'] == 'asyncy/asyncy-node'
    assert container.aliases['python'] == 'asyncy/asyncy-python'


def test_containers_alias(container):
    container.aliases = {'simple': 'complex'}
    assert container.alias('simple') == 'complex'


def test_containers_alias_empty(container):
    container.alias('empty') == 'empty'


def test_containers_run(logger, docker_mock, container):
    container.run(logger)
    logger.log.assert_called_with('container-run', 'hello-world')
    docker_mock.containers.run.assert_called_with('hello-world', command=())
    docker_mock.images.pull.assert_called_with('hello-world')
    assert container.output == docker.from_env().containers.run()


def test_containers_run_commands(logger, docker_mock, container):
    container.run(logger, 'one', 'two')
    containers = docker_mock.containers.run
    containers.assert_called_with('hello-world', command=())


def test_containers_results(container):
    container.output = 'output'
    assert container.result() == 'output'
