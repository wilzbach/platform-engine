# -*- coding: utf-8 -*-
from asyncy.Github import Github
from asyncy.models import BaseModel, Repositories, Stories

from peewee import CharField, ForeignKeyField

from pytest import fixture

from storyscript import resolver
from storyscript.parser import Parser


@fixture
def story(user):
    repo = Repositories(name='project', organization='org', owner=user)
    return Stories(filename='my.story', repository=repo)


def test_stories():
    assert Stories.version.null
    assert isinstance(Stories.filename, CharField)
    assert isinstance(Stories.version, CharField)
    assert isinstance(Stories.repository, ForeignKeyField)
    assert issubclass(Stories, BaseModel)


def test_stories_backend(mocker, story):
    mocker.patch.object(Github, '__init__', return_value=None)
    mocker.patch.object(Github, 'authenticate')
    story.backend('app_id', 'pem_path', 'installation_id')
    Github.__init__.assert_called_with('app_id', 'pem_path')
    Github.authenticate.assert_called_with('installation_id')
    assert isinstance(story.github, Github)


def test_stories_get_contents(magic, story):
    story.github = magic()
    result = story.get_contents()
    repository = story.repository
    args = (repository.organization, repository.name, story.filename)
    story.github.get_contents.assert_called_with(*args, version=story.version)
    assert result == story.github.get_contents()


def test_stories_data(story):
    story.data({})
    assert story._initial_data == {}


def test_stories_build_tree(mocker, story):
    mocker.patch.object(Parser, '__init__', return_value=None)
    mocker.patch.object(Parser, 'parse')
    mocker.patch.object(Stories, 'get_contents')
    story.build_tree()
    Stories.get_contents.assert_called_with()
    assert story.tree == Parser.parse().json()


def test_stories_line(story):
    story.tree = {'script': {'1': 'line one'}}
    assert story.line('1') == story.tree['script']['1']


def test_stories_resolve(mocker, magic, story):
    mocker.patch.object(resolver, 'resolve_obj')
    mocker.patch.object(Stories, 'line')
    story._initial_data = {}
    result = story.resolve('1')
    Stories.line.assert_called_with('1')
    resolver.resolve_obj.assert_called_with({}, Stories.line()['args'])
    assert result == resolver.resolve_obj()
