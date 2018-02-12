# -*- coding: utf-8 -*-
from asyncy.models import BaseModel, Repositories, Stories

from peewee import CharField, ForeignKeyField

from pytest import fixture, mark

from storyscript.parser import Parser
from storyscript.resolver import Resolver


@fixture
def story(repository):
    return Stories(filename='my.story', repository=repository)


def test_stories():
    assert Stories.version.null
    assert isinstance(Stories.filename, CharField)
    assert isinstance(Stories.version, CharField)
    assert isinstance(Stories.repository, ForeignKeyField)
    assert issubclass(Stories, BaseModel)


def test_stories_backend(mocker, story):
    mocker.patch.object(Repositories, 'backend')
    story.backend('app_id', 'pem_path', 'install_id')
    Repositories.backend.assert_called_with('app_id', 'pem_path', 'install_id')


def test_stories_get_contents(mocker, story):
    mocker.patch.object(Repositories, 'contents')
    result = story.get_contents()
    Repositories.contents.assert_called_with(story.filename, story.version)
    assert result == Repositories.contents()


def test_stories_data(story):
    story.data({})
    assert story._initial_data == {}


def test_stories_environment(mocker, story):
    mocker.patch.object(Repositories, 'config', return_value={'env': 'env'})
    assert story.environment() == 'env'


@mark.parametrize('env', [None, {}])
def test_stories_environment_none(mocker, story, env):
    mocker.patch.object(Repositories, 'config', return_value=env)
    assert story.environment() == {}


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


def test_stories_resolve(mocker, logger, magic, story):
    mocker.patch.object(Resolver, 'resolve')
    mocker.patch.object(Stories, 'line', return_value={'args': {}})
    story._initial_data = {}
    result = story.resolve(logger, '1')
    Stories.line.assert_called_with('1')
    Resolver.resolve.assert_called_with(Stories.line()['args'], {})
    logger.log.assert_called_with('story-resolve', {}, Resolver.resolve())
    assert result == Resolver.resolve()


def test_stories_build(patch, application, story):
    patch.object(Stories, 'data')
    patch.object(Stories, 'backend')
    patch.object(Stories, 'build_tree')
    story.build(application, '123', 'path')
    Stories.data.assert_called_with(application.initial_data)
    Stories.backend.assert_called_with('123', 'path',
                                       application.installation_id())
    Stories.build_tree.assert_called_with()
