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
    echo_line['service'] = 'alpine-echo'
    echo_service['alpine-echo'] = echo_service['alpine']

    story.prepare()
    result = await Containers.exec(logger, story, echo_line,
                                   'alpine-echo', 'echo')
    assert result == '{"msg":"foo"}'


async def clean_container(story, line):
    await Containers.stop_container(
        story, line, Containers.get_container_name(line['service']))

    await Containers.remove_container(
        story, line, Containers.get_container_name(line['service']),
        force=True)


@mark.asyncio
async def test_start(logger, config, story, echo_service, echo_line):
    story.app = App(config, logger)
    story.app.services = echo_service

    story.prepare()

    await clean_container(story, echo_line)

    result = await Containers.start(story, echo_line)
    assert result.container_name == Containers.get_container_name(
        echo_line['service'])
    assert result.name == echo_line['service']
    assert result.command == echo_line['command']
    assert result.hostname is not None

    await clean_container(story, echo_line)


def test_containers_format_command(story):
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
    assert Containers.format_command(
        story, story.line('1'), 'alpine', 'echo'
    ) == ['echo', '{"msg":"foo"}']


def test_containers_format_command_no_arguments(story):
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
    assert Containers.format_command(
        story, story.line('1'), 'alpine', 'echo'
    ) == ['echo']
