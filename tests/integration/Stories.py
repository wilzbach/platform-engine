# -*- coding: utf-8 -*-
import json

from asyncy.Config import Config
from asyncy.Logger import Logger
from asyncy.Stories import Stories

from pytest import fixture, raises

import requests

from storyscript.parser import Parser


@fixture
def config():
    return Config()


@fixture
def logger(config):
    logger = Logger(config)
    logger.start()
    return logger


@fixture
def story(config, logger):
    return Stories(config, logger, 1, 'hello.story')


@fixture
def api_response():
    response = None
    with open('tests/integration/hello.story.json', 'r') as f:
        response = json.load(f)
    return response


def test_stories_get(patch, magic, story, api_response):
    # NOTE(vesuvium): there's no simple way to run an http server and
    # have it return a specific response within testing, so requests is mocked
    response = magic(json=magic(return_value=api_response))
    patch.object(requests, 'get', return_value=response)
    story.get()
    assert story.tree is not None
    assert story.environment == {'name': 'Asyncy'}
    assert story.containers == {}
    assert story.repository == {'url': 'https://github.com/asyncy/stories.git'}
    assert story.version is None


def test_stories_resolve_simple(story):
    """
    Ensures a simple resolve can be performed
    """
    story_text = 'alpine echo "hello"'
    story.environment = {}
    story.tree = Parser().parse(story_text).json()
    assert story.resolve('1') == 'echo hello'


def test_stories_resolve_replacement(patch, magic, story, api_response):
    """
    Ensures a replacement resolve can be performed
    """
    response = magic(json=magic(return_value=api_response))
    patch.object(requests, 'get', return_value=response)
    story.get()
    assert story.resolve('1') == 'echo Hi, I am Asyncy!'


def test_stories_resolve_replace_error(patch, magic, story, api_response):
    """
    Ensures a ValueError is raised when the environment does not provide enough
    data
    """
    response = magic(json=magic(return_value=api_response))
    patch.object(requests, 'get', return_value=response)
    story.get()
    story.environment = {}
    with raises(ValueError):
        story.resolve('1')
