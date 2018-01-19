# -*- coding: utf-8 -*-
from evenflow.Github import Github
from evenflow.models import BaseModel, Repositories, Stories

from peewee import CharField, ForeignKeyField

from pytest import fixture

from storyscript import resolver
from storyscript.parser import Parser


@fixture
def story():
    repo = Repositories(name='project', owner='user')
    return Stories(filename='my.story', repository=repo)


def test_stories():
    assert Stories.version.null
    assert isinstance(Stories.filename, CharField)
    assert isinstance(Stories.version, CharField)
    assert isinstance(Stories.repository, ForeignKeyField)
    assert issubclass(Stories, BaseModel)


def test_stories_provider(mocker, story):
    mocker.patch.object(Github, '__init__', return_value=None)
    story.provider('app_id', 'app_name', 'pem_path')
    Github.__init__.assert_called_with('app_id', 'pem_path', 'app_name')
    assert isinstance(story.github, Github)


def test_stories_get(mocker, story):
    story.github = mocker.MagicMock()
    result = story.get_contents()
    args = (story.repository.owner, story.repository.name, story.filename)
    story.github.get_contents.assert_called_with(*args, version=story.version)
    assert result == story.github.get_contents()


def test_stories_build_tree(mocker, story):
    mocker.patch.object(Parser, '__init__', return_value=None)
    mocker.patch.object(Parser, 'parse')
    mocker.patch.object(Stories, 'get_contents')
    story.build_tree()
    Stories.get_contents.assert_called_with()
    assert story.tree == Parser.parse().json()


def test_stories_resolve(mocker, story):
    mocker.patch.object(resolver, 'resolve_obj')
    args = mocker.MagicMock()
    story.tree = {'story': {1: {'args': args}}}
    result = story.resolve(1, {})
    resolver.resolve_obj.assert_called_with({}, args)
    assert result == resolver.resolve_obj()
