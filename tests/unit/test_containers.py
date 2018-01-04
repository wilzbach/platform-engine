# -*- coding: utf-8 -*-
import docker

from evenflow.Containers import Containers

from pytest import fixture


@fixture
def container():
    return Containers('hello-world')


def test_container(container):
    assert container.name == 'hello-world'


def test_docker_run(mocker, container):
    mocker.patch.object(docker, 'from_env')
    container.run()
    docker.from_env().containers.run.assert_called_with()
