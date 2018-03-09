# -*- coding: utf-8 -*-
from asyncy.Config import Config
from asyncy.Logger import Logger
from asyncy.Stories import Stories

from pytest import fixture, raises

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


def test_stories_resolve_simple(story):
    """
    Ensures a simple resolve can be performed
    """
    story_text = 'alpine echo "hello"'
    story.environment = {}
    story.tree = Parser().parse(story_text).json()
    assert story.resolve('1') == 'echo hello'


def test_stories_resolve_replacement(story):
    """
    Ensures a replacement resolve can be performed
    """
    story_text = 'alpine echo "{{name}}"'
    story.environment = {'name': 'asyncy'}
    story.tree = Parser().parse(story_text).json()
    assert story.resolve('1') == 'echo asyncy'


def test_stories_resolve_replace_value_error(story):
    """
    Ensures a ValueError is raised when the environment does not provide enough
    data
    """
    story_text = 'alpine echo "{{name}}"'
    story.environment = {}
    story.tree = Parser().parse(story_text).json()
    with raises(ValueError):
        story.resolve('1')
