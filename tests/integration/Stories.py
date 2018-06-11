# -*- coding: utf-8 -*-
from asyncy.Stories import Stories

from pytest import fixture

from storyscript.parser import Parser

import ujson

from . import examples


def test_stories_get(patch, magic, story):
    assert story.tree is not None
    assert story.context is None
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
    story.tree = Parser().parse(story_text).json()['script']
    assert story.resolve_command(story.line('1')) == "-c 'print(\'hello\')'"


def test_stories_resolve_command_no_commands(story):
    story_text = 'alpine echo "hello"'
    story.context = {}
    story.containers = {'alpine': {'commands': {}}}
    story.tree = Parser().parse(story_text).json()['script']
    assert story.resolve_command(story.line('1')) == "echo 'hello'"


def test_stories_resolve_replacement(patch, magic, story):
    """
    Ensures a replacement resolve can be performed
    """
    assert story.resolve(
        story.line('1')['args'][1],
        encode=False
    ) == 'Hi, I am Asyncy!'

    assert story.resolve(
        story.line('1')['args'][1],
        encode=True
    ) == "'Hi, I am Asyncy!'"
