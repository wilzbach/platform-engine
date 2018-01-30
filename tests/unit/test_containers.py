# -*- coding: utf-8 -*-
from asyncy.Containers import Containers

import docker

from pytest import fixture


@fixture
def container(mocker):
    mocker.patch.object(Containers, 'alias', return_value='hello-world')
    return Containers('hello-world')


@fixture
def docker_mock(mocker):
    mocker.patch.object(docker, 'from_env')
    return docker.from_env()


def test_containers(container):
    Containers.alias.assert_called_with('hello-world')
    assert container.name == Containers.alias()


def test_containers_aliases(container):
    assert container.aliases['node'] == 'asyncy/asyncy-node'
    assert container.aliases['python'] == 'asyncy/asyncy-python'


def test_containers_alias():
    container = Containers('name')
    container.aliases = {'simple': 'complex'}
    assert container.alias('simple') == 'complex'


def test_containers_alias_empty(container):
    container.alias('empty') == 'empty'


def test_containers_environment(patch, story, application, container):
    patch.object(application, 'environment', return_value={'one': 1, 'two': 2})
    patch.object(story, 'environment', return_value={'two': 0, 'three': 3})
    container.environment(application, story)
    application.environment.assert_called_with()
    story.environment.assert_called_with()
    assert container.env == {'one': 1, 'two': 0, 'three': 3}


def test_containers_run(logger, docker_mock, container):
    container.run(logger, {})
    logger.log.assert_called_with('container-run', 'hello-world')
    kwargs = {'command': (), 'environment': {}}
    docker_mock.containers.run.assert_called_with('hello-world', **kwargs)
    docker_mock.images.pull.assert_called_with('hello-world')
    assert container.output == docker.from_env().containers.run()


def test_containers_run_commands(logger, docker_mock, container):
    container.run(logger, {}, 'one', 'two')
    containers = docker_mock.containers.run
    containers.assert_called_with('hello-world', command=(), environment={})


def test_containers_results(container):
    container.output = 'output'
    assert container.result() == 'output'
