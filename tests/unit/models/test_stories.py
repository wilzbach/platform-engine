# -*- coding: utf-8 -*-
from evenflow.models import BaseModel, Repositories, Stories

from peewee import CharField, ForeignKeyField

import requests


def test_stories():
    assert Stories.version.null
    assert isinstance(Stories.filename, CharField)
    assert isinstance(Stories.version, CharField)
    assert isinstance(Stories.repository, ForeignKeyField)
    assert isinstance(Stories.application, ForeignKeyField)
    assert issubclass(Stories, BaseModel)


def test_stories_get(mocker):
    mocker.patch.object(requests, 'get')
    repo = Repositories(name='project', owner='user')
    story = Stories(filename='my.story', repository=repo, application='app')
    story.get_contents()
    api_url = 'https://api.github.com/repos/user/project/contents/my.story'
    requests.get.assert_called_with(api_url, params={'ref': story.version})
