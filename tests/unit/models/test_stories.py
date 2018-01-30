# -*- coding: utf-8 -*-
from asyncy.models import BaseModel, Repositories, Stories

from peewee import CharField, ForeignKeyField

from pytest import fixture, mark

from storyscript import resolver
from storyscript.parser import Parser


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
    assert story.environment() is None


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
    mocker.patch.object(resolver, 'resolve_obj')
    mocker.patch.object(Stories, 'line', return_value={'args': {}})
    story._initial_data = {}
    result = story.resolve(logger, '1')
    Stories.line.assert_called_with('1')
    resolver.resolve_obj.assert_called_with({}, Stories.line()['args'])
    logger.log.assert_called_with('story-resolve', {}, resolver.resolve_obj())
    assert result == resolver.resolve_obj()
