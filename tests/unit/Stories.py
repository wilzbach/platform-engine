# -*- coding: utf-8 -*-
import time

from asyncy.Stories import Stories
from asyncy.utils import Http

from storyscript.resolver import Resolver


def test_stories_init(config, logger, story):
    assert story.app_id == 1
    assert story.name == 'hello.story'
    assert story.config == config
    assert story.logger == logger
    assert story.results == {}


def test_stories_get(patch, config, story):
    patch.object(Http, 'get')
    story.get()
    url = 'http://{}/apps/1/stories/hello.story'.format(config.api_url)
    Http.get.assert_called_with(url, json=True)
    assert story.tree == Http.get()['tree']
    assert story.environment == Http.get()['environment']
    assert story.containers == Http.get()['containers']
    assert story.repository == Http.get()['repository']
    assert story.version == Http.get()['version']


def test_stories_line(magic, story):
    story.tree = magic()
    line = story.line('1')
    assert line == story.tree['script']['1']


def test_stories_resolve(patch, logger, story):
    patch.object(Stories, 'line')
    patch.object(Resolver, 'resolve')
    story.environment = 'environment'
    result = story.resolve('1')
    Stories.line.assert_called_with('1')
    Resolver.resolve.assert_called_with(Stories.line()['args'],
                                        story.environment)
    logger.log.assert_called_with('story-resolve', Stories.line()['args'],
                                  Resolver.resolve())
    assert result == Resolver.resolve()


def test_stories_start_line(patch, story):
    patch.object(time, 'time')
    story.start_line('1')
    assert story.results['1'] == {'start': time.time()}


def test_stories_end_line(patch, story):
    patch.object(time, 'time')
    story.results = {'1': {'start': 'start'}}
    story.end_line('1', 'output')
    assert story.results['1']['output'] == 'output'
    assert story.results['1']['end'] == time.time()
    assert story.results['1']['start'] == 'start'
