# -*- coding: utf-8 -*-
from evenflow.models import BaseModel, Repositories, Stories

from peewee import CharField, ForeignKeyField

from pytest import fixture

import requests

import storyscript


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
