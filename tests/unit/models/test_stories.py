# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from evenflow.models import BaseModel, Repositories, Stories

from peewee import CharField, ForeignKeyField

from pytest import fixture

import requests

import storyscript
from storyscript import resolver


@fixture
def story():
    repo = Repositories(name='project', owner='user')
    return Stories(filename='my.story', repository=repo, application='app')


def test_stories():
    assert Stories.version.null
    assert isinstance(Stories.filename, CharField)
    assert isinstance(Stories.version, CharField)
    assert isinstance(Stories.repository, ForeignKeyField)
    assert isinstance(Stories.application, ForeignKeyField)
    assert issubclass(Stories, BaseModel)


def test_stories_get(mocker, story):
    mocker.patch.object(requests, 'get')
    story.get_contents()
    api_url = 'https://api.github.com/repos/user/project/contents/my.story'
    requests.get.assert_called_with(api_url, params={'ref': story.version})


def test_stories_build_tree(mocker, story):
    mocker.patch.object(storyscript, 'parse')
    mocker.patch.object(Stories, 'get_contents')
    story.build_tree()
    storyscript.parse().json.assert_called_with()
    assert story.tree == storyscript.parse().json()


def test_stories_resolve(mocker, story):
    mocker.patch.object(resolver, 'resolve_obj')
    args = MagicMock()
    story.tree = {'story': {1: {'args': args}}}
    result = story.resolve(1, {})
    resolver.resolve_obj.assert_called_with({}, args)
    assert result == resolver.resolve_obj()
