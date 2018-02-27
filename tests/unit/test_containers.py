# -*- coding: utf-8 -*-
from asyncy.Containers import Containers

import docker

from pytest import fixture, raises


@fixture
def client(patch):
    patch.object(docker, 'from_env')
    return docker.from_env()


@fixture
def container(patch, logger, client):
    patch.object(Containers, 'alias', return_value='name')
    return Containers('hello-world', logger)


def test_containers(patch, logger, client):
    patch.object(Containers, 'alias')
    container = Containers('hello-world', logger)
    Containers.alias.assert_called_with('hello-world')
    assert container.client == docker.from_env()
    assert container.name == Containers.alias()
    assert container.env == {}
    assert container.volume is None
    assert container.logger == logger


def test_containers_aliases(container):
    assert container.aliases['node'] == 'asyncy/asyncy-node'
    assert container.aliases['python'] == 'asyncy/asyncy-python'


def test_containers_alias(logger):
    container = Containers('name', logger)
    container.aliases = {'simple': 'complex'}
    assert container.alias('simple') == 'complex'


def test_containers_alias_empty(logger):
    container = Containers('name', logger)
    container.alias('empty') == 'empty'


def test_containers_make_volume(container):
    container.make_volume('volume')
    container.client.volumes.get.assert_called_with('volume')
    assert container.volume == container.client.volumes.get()


def test_containers_make_volume_create(container):
    container.client.volumes.get.side_effect = docker.errors.NotFound('')
    container.make_volume('volume')
    container.client.volumes.create.assert_called_with('volume')
    assert container.volume == container.client.volumes.create()


def test_containers_run(magic, logger, client, container):
    container.volume = magic(name='volume')
    container.run(logger, 'command', {})
    kwargs = {'command': 'command', 'environment': {},
              'cap_drop': 'all',
              'volumes': {container.volume.name: {'bind': '/opt/v1',
                                                  'mode': 'rw'}}}
    client.containers.run.assert_called_with(container.name, **kwargs)
    client.images.pull.assert_called_with(container.name)
    assert logger.log.call_count == 2
    assert container.output == client.containers.run()


def test_containers_results(container):
    container.output = 'output'
    assert container.result() == 'output'
