# -*- coding: utf-8 -*-
from asyncy.App import App
from asyncy.Containers import Containers
from asyncy.constants.ServiceConstants import ServiceConstants

from pytest import mark

from storyscript.compiler import Compiler
from storyscript.parser import Parser


@mark.asyncio
async def test_exec(logger, config, story, echo_service, echo_line):
    story.app = App(config, logger)
    story.app.services = echo_service

    story.prepare()
    result = await Containers.exec(logger, story, echo_line,
                                   'asyncy--echo', 'echo')

    assert result == '{"msg":"foo"}'


@mark.asyncio
async def test_containers_format_command(story):
    """
    Ensures a simple resolve can be performed
    """
    story_text = 'alpine echo msg:"foo"\n'
    story.context = {}
    story.app.services = {
        'alpine': {
            ServiceConstants.config: {
                'commands': {
                    'echo': {
                        'arguments': {'msg': {'type': 'string'}}
                    }
                }
            }
        }
    }

    story.tree = Compiler.compile(Parser().parse(story_text))['tree']
    assert await Containers.format_command(
        story, story.line('1'), 'alpine', 'echo'
    ) == ['echo', '{"msg":"foo"}']


@mark.asyncio
async def test_containers_format_command_no_arguments(story):
    story_text = 'alpine echo\n'
    story.context = {}
    story.app.services = {
        'alpine': {
            ServiceConstants.config: {
                'commands': {
                    'echo': {}
                }
            }
        }
    }
    story.tree = Compiler.compile(Parser().parse(story_text))['tree']
    assert await Containers.format_command(
        story, story.line('1'), 'alpine', 'echo'
    ) == ['echo']
