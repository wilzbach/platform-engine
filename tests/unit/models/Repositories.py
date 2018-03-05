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


def test_repositories_config(patch, magic, repository):
    patch.object(Yaml, 'string', return_value={'globals': 'g', 'story': 's'})
    repository.github = magic()
    result = repository.config('story')
    repository.github.get_contents.assert_called_with(repository.organization,
                                                      repository.name,
                                                      'asyncy.yml')
    Yaml.string.assert_called_with(repository.github.get_contents())
    assert result == {'globals': 'g', 'story': 's'}


def test_repositories_config_no_globals(patch, magic, repository):
    patch.object(Yaml, 'string', return_value={'story': 's'})
    repository.github = magic()
    result = repository.config('story')
    assert result == {'story': 's'}


def test_repositories_config_no_story(patch, magic, repository):
    patch.object(Yaml, 'string', return_value={'globals': 'g'})
    repository.github = magic()
    result = repository.config('story')
    assert result == {'globals': 'g'}


def test_repositories_config_none(magic, repository):
    repository.github = magic(get_contents=magic(return_value=None))
    assert repository.config('story') == {}
