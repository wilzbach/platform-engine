# -*- coding: utf-8 -*-
from storyscript.compiler import Compiler
from storyscript.parser import Parser

from asyncy.App import App
from asyncy.Containers import Containers

from pytest import mark


@mark.asyncio
async def test_exec(logger, config, story, echo_service, echo_line):
    story.app = App(config, logger)
    story.app.services = echo_service

    story.prepare()
    result = await Containers.exec(logger, story, echo_line,
                                   'asyncy--echo', 'echo')

    assert result == '{"msg":"foo"}'


def test_containers_format_command(story):
    """
    Ensures a simple resolve can be performed
    """
    story_text = 'alpine echo msg:"foo"\n'
    story.context = {}
    story.app.services = {
        'alpine': {
            'config': {
                'commands': {
                    'echo': {
                        'arguments': {'msg': {'type': 'string'}}
                    }
                }
            }
        }
    }

    story.tree = Compiler.compile(Parser().parse(story_text))['tree']
    assert Containers.format_command(
        story, story.line('1'), 'alpine', 'echo'
    ) == ['echo', '{"msg":"foo"}']


def test_containers_format_command_no_arguments(story):
    story_text = 'alpine echo\n'
    story.context = {}
    story.app.services = {
        'alpine': {
            'config': {
                'commands': {
                    'echo': {}
                }
            }
        }
    }
    story.tree = Compiler.compile(Parser().parse(story_text))['tree']
    assert Containers.format_command(
        story, story.line('1'), 'alpine', 'echo'
    ) == ['echo']
