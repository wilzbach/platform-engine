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
    assert story.tree is not None
    assert story.context == {'name': 'Asyncy'}
    assert 'pull_url' in story.containers['alpine']
    assert 'echo' in story.containers['alpine']['commands']
    assert story.repository == {'url': 'https://github.com/asyncy/stories.git'}
    assert story.version is None


def test_stories_resolve_command(story):
    """
    Ensures a simple resolve can be performed
    """
    story_text = 'alpine echo "hello"'
    story.context = {}
    story.containers = {'alpine': {'commands': {
        'echo': {'args': [{'type': 'string'}]}
    }}}
    story.tree = Parser().parse(story_text).json()
    assert story.resolve_command(story.line('1')) == "echo 'hello'"


def test_stories_resolve_command_no_commands_nested_string(story):
    story_text = 'python -c "print(\'hello\')"'
    story.context = {}
    story.containers = {'python': {'pull_url': 'asyncy/asyncy-python',
                        'commands': {}}}
    story.tree = Parser().parse(story_text).json()
    assert story.resolve_command(story.line('1')) == "-c 'print(\'hello\')'"


def test_stories_resolve_command_no_commands(story):
    story_text = 'alpine echo "hello"'
    story.context = {}
    story.containers = {'alpine': {'commands': {}}}
    story.tree = Parser().parse(story_text).json()
    assert story.resolve_command(story.line('1')) == "echo 'hello'"


def test_stories_resolve_replacement(patch, magic, story, api_response):
    """
    Ensures a replacement resolve can be performed
    """
    response = magic(json=magic(return_value=api_response('hello.story.json')))
    patch.object(requests, 'get', return_value=response)
    assert story.resolve(
        story.line('1')['args'][1],
        encode=False
    ) == 'Hi, I am Asyncy!'

    assert story.resolve(
        story.line('1')['args'][1],
        encode=True
    ) == "'Hi, I am Asyncy!'"
