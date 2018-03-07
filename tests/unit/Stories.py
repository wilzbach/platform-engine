# -*- coding: utf-8 -*-
from asyncy.Stories import Stories
from asyncy.utils import Http


def test_stories_init(logger, story):
    assert story.app_id == 1
    assert story.name == 'hello.story'
    assert story.logger == logger


def test_stories_get(patch, story):
    patch.object(Http, 'get')
    story.get()
    url = 'http://api/apps/1/stories/hello.story'
    Http.get.assert_called_with(url, json=True)
    assert story.tree == Http.get()['tree']
    assert story.environment == Http.get()['environment']
    assert story.containers == Http.get()['containers']
    assert story.repository == Http.get()['repository']
