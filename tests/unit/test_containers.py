# -*- coding: utf-8 -*-
from asyncy.Containers import Containers

import docker

from pytest import fixture


@fixture
def client(patch):
    patch.object(docker, 'from_env')
    return docker.from_env()


@fixture
def container(patch, client):
    patch.object(Containers, 'alias', return_value='name')
    return Containers('hello-world')


def test_containers(patch, client):
    patch.object(Containers, 'alias')
    container = Containers('hello-world')
    Containers.alias.assert_called_with('hello-world')
    assert container.client == docker.from_env()
    assert container.name == Containers.alias()
    assert container.env == {}


def test_containers_aliases(container):
    assert container.aliases['node'] == 'asyncy/asyncy-node'
    assert container.aliases['python'] == 'asyncy/asyncy-python'


def test_containers_alias():
    container = Containers('name')
    container.aliases = {'simple': 'complex'}
    assert container.alias('simple') == 'complex'


def test_containers_alias_empty():
    container = Containers('name')
    container.alias('empty') == 'empty'


def test_containers_environment(patch, story, application, container):
    patch.object(application, 'environment', return_value={'one': 1, 'two': 2})
    patch.object(story, 'environment', return_value={'two': 0, 'three': 3})
    container.environment(application, story)
    application.environment.assert_called_with()
    story.environment.assert_called_with()
    assert container.env == {'one': 1, 'two': 0, 'three': 3}


def test_containers_run(logger, client, container):
    container.run(logger, {})
    logger.log.assert_called_with('container-run', container.name)
    kwargs = {'command': (), 'environment': {}}
    client.containers.run.assert_called_with(container.name, **kwargs)
    client.images.pull.assert_called_with(container.name)
    assert container.output == client.containers.run()


def test_containers_run_commands(logger, client, container):
    container.run(logger, 'one', 'two')
    containers = client.containers.run
    containers.assert_called_with(container.name, command=(), environment={})


def test_containers_results(container):
    container.output = 'output'
    assert container.result() == 'output'
