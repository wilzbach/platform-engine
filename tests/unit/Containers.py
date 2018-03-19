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
    return Containers(logger, 'containers', 'hello-world')


def test_containers_init(patch, logger, client):
    patch.object(Containers, 'alias')
    container = Containers(logger, 'containers', 'hello-world')
    Containers.alias.assert_called_with('hello-world')
    assert container.client == docker.from_env()
    assert container.name == Containers.alias()
    assert container.containers == 'containers'
    assert container.env == {}
    assert container.volume is None
    assert container.logger == logger


def test_containers_alias(logger):
    container = Containers(logger, 'containers', 'name')
    container.containers = {'simple': {'pull_url': 'hub.docker.container'}}
    assert container.alias('simple') == 'hub.docker.container'


def test_containers_alias_empty(logger):
    container = Containers(logger, 'containers', 'name')
    container.alias('empty') == 'empty'


def test_containers_image(container):
    container.image('image')
    container.client.images.get.assert_called_with('image')


def test_containers_image_pull(container):
    container.client.images.get.side_effect = docker.errors.ImageNotFound('')
    container.image('image')
    container.client.images.pull.assert_called_with('image')


def test_containers_make_volume(container):
    container.make_volume('volume')
    container.client.volumes.get.assert_called_with('volume')
    container.logger.log.assert_called_with('container-volume', 'volume')
    assert container.volume == container.client.volumes.get()


def test_containers_make_volume_create(container):
    container.client.volumes.get.side_effect = docker.errors.NotFound('')
    container.make_volume('volume')
    container.client.volumes.create.assert_called_with('volume')
    assert container.volume == container.client.volumes.create()


def test_containers_summon(patch, magic, client, container):
    patch.object(Containers, 'image')
    container.volume = magic(name='volume')
    container.summon('command', {})
    kwargs = {'command': 'command', 'environment': {},
              'cap_drop': 'all',
              'volumes': {container.volume.name: {'bind': '/opt/v1',
                                                  'mode': 'rw'}}}
    client.containers.run.assert_called_with(container.name, **kwargs)
    Containers.image.assert_called_with(container.name)
    assert container.logger.log.call_count == 2
    assert container.output == client.containers.run()


def test_containers_results(container):
    container.output = 'output'
    assert container.result() == 'output'


def test_containers_run(patch, logger, story):
    patch.init(Containers)
    patch.many(Containers, ['make_volume', 'summon', 'result'])
    story.containers = {}
    story.environment = {}
    result = Containers.run(logger, story, 'name', 'command')
    Containers.__init__.assert_called_with(logger, story.containers, 'name')
    Containers.make_volume.assert_called_with(story.name)
    Containers.summon.assert_called_with('command', story.environment)
    assert result == Containers.result()
