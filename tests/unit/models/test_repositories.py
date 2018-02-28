# -*- coding: utf-8 -*-
from asyncy.Github import Github
from asyncy.models import BaseModel, Repositories
from asyncy.utils import Yaml

from peewee import CharField, ForeignKeyField


def test_repositories():
    assert isinstance(Repositories.name, CharField)
    assert isinstance(Repositories.organization, CharField)
    assert isinstance(Repositories.owner, ForeignKeyField)
    assert issubclass(Repositories, BaseModel)


def test_repositores_backend(patch, logger, repository):
    patch.object(Github, '__init__', return_value=None)
    patch.object(Github, 'authenticate')
    repository.backend(logger, 'app_id', 'pem_path', 'installation_id')
    Github.__init__.assert_called_with(logger, 'app_id', 'pem_path')
    Github.authenticate.assert_called_with('installation_id')
    assert isinstance(repository.github, Github)


def test_repositories_contents(magic, repository):
    repository.github = magic()
    result = repository.contents('filename', 'version')
    args = (repository.organization, repository.name, 'filename')
    repository.github.get_contents.assert_called_with(*args, version='version')
    assert result == repository.github.get_contents()


def test_repositories_config(mocker, magic, repository):
    mocker.patch.object(Yaml, 'string')
    repository.github = magic()
    result = repository.config()
    repository.github.get_contents.assert_called_with(repository.organization,
                                                      repository.name,
                                                      'asyncy.yml')
    Yaml.string.assert_called_with(repository.github.get_contents())
    assert result == Yaml.string()


def test_repositories_config_none(mocker, magic, repository):
    repository.github = magic(get_contents=magic(return_value=None))
    assert repository.config() is None
