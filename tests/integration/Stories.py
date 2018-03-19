# -*- coding: utf-8 -*-
from asyncy.Stories import Stories

from pytest import fixture, raises

import requests

from storyscript.parser import Parser


@fixture
def story(config, logger):
    return Stories(config, logger, 1, 'hello.story')


def test_stories_get(patch, magic, story, patch_request):
    patch_request('hello.story.json')
    story.get()
    assert story.tree is not None
    assert story.environment == {'name': 'Asyncy'}
    assert story.containers['alpine']['real_name'] == 'alpine'
    assert 'echo' in story.containers['alpine']['commands']
    assert story.repository == {'url': 'https://github.com/asyncy/stories.git'}
    assert story.version is None


def test_stories_resolve_simple(story):
    """
    Ensures a simple resolve can be performed
    """
    story_text = 'alpine echo "hello"'
    story.environment = {}
    story.containers = {'alpine': {'commands': {
        'echo': {'args': {'message': 'string'}}
    }}}
    story.tree = Parser().parse(story_text).json()
    assert story.resolve_command(story.line('1')) == 'echo "hello"'


def test_stories_resolve_replacement(patch, magic, story, api_response):
    """
    Ensures a replacement resolve can be performed
    """
    response = magic(json=magic(return_value=api_response('hello.story.json')))
    patch.object(requests, 'get', return_value=response)
    story.get()
    assert story.resolve(story.line('1')['args'][1]) == 'Hi, I am Asyncy!'


def test_stories_resolve_replace_error(patch, magic, story, api_response):
    """
    Ensures a ValueError is raised when the environment does not provide enough
    data
    """
    response = magic(json=magic(return_value=api_response('hello.story.json')))
    patch.object(requests, 'get', return_value=response)
    story.get()
    story.environment = {}
    with raises(ValueError):
        story.resolve(story.line('1')['args'])
