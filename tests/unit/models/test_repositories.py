# -*- coding: utf-8 -*-
from asyncy.Github import Github
from asyncy.models import BaseModel, Repositories

from peewee import CharField, ForeignKeyField


def test_repositories():
    assert isinstance(Repositories.name, CharField)
    assert isinstance(Repositories.organization, CharField)
    assert isinstance(Repositories.owner, ForeignKeyField)
    assert issubclass(Repositories, BaseModel)


def test_repositores_backend(mocker, repository):
    mocker.patch.object(Github, '__init__', return_value=None)
    mocker.patch.object(Github, 'authenticate')
    repository.backend('app_id', 'pem_path', 'installation_id')
    Github.__init__.assert_called_with('app_id', 'pem_path')
    Github.authenticate.assert_called_with('installation_id')
    assert isinstance(repository.github, Github)


def test_repositories_contents(magic, repository):
    repository.github = magic()
    result = repository.contents('filename', 'version')
    args = (repository.organization, repository.name, 'filename')
    repository.github.get_contents.assert_called_with(*args, version='version')
    assert result == repository.github.get_contents()
