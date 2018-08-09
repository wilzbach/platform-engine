# -*- coding: utf-8 -*-
from collections import deque

from asyncy.Exceptions import AsyncyError
from asyncy.constants.LineConstants import LineConstants as L
from asyncy.processing.Services import Services, Service, Command, Event

import pytest
from pytest import mark


@mark.asyncio
async def test_services_execute(story, async_mock):
    handler = async_mock(return_value='output')

    Services.register_internal('my_service', 'my_command', {}, 'any', handler)

    assert Services.is_internal('my_service') is True
    line = {
        L.service: 'my_service',
        L.command: 'my_command'
    }

    assert await Services.execute(story, line) == 'output'


@mark.asyncio
async def test_services_execute_invalid_command(story):
    Services.register_internal('my_service', 'my_command', {}, 'any', None)

    line = {
        L.service: 'my_service',
        L.command: 'foo_command'
    }

    with pytest.raises(AsyncyError):
        await Services.execute(story, line)


@mark.asyncio
async def test_services_execute_args(story, async_mock):
    handler = async_mock(return_value='output')

    Services.register_internal('my_service', 'my_command',
                               {'arg1': {'type': 'string'}},
                      'any', handler)

    assert Services.is_internal('my_service') is True
    line = {
        L.service: 'my_service',
        L.command: 'my_command',
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'arg1',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'Hello world!'
                }
            }
        ]
    }

    assert await Services.execute(story, line) == 'output'
    handler.mock.assert_called_with(story=story, line=line,
                                    resolved_args={'arg1': 'Hello world!'})


def test_services_log_registry(logger):
    Services.init(logger)
    Services.register_internal('my_service', 'my_command', {}, 'any', None)
    Services.log_internal()
    logger.log_raw.assert_called_with(
        'info', 'Discovered internal service my_service - [\'my_command\']')


def test_resolve_chain(story):
    """
    The story tested here is:
    alpine echo as client
        when client foo as echo_helper
            alpine echo
                echo_helper sonar  # This isn't possible, but OK.
            echo_helper sonar

    """
    story.app.services = {
        'alpine': {} 
    }
    
    story.tree = {
        '1': {
            L.method: 'execute',
            L.service: 'alpine',
            L.command: 'echo',
            L.enter: '2',
            L.output: ['client']
        },
        '2': {
            L.method: 'when',
            L.service: 'client',
            L.command: 'foo',
            L.parent: '1',
            L.output: ['echo_helper']
        },
        '3': {
            L.method: 'execute',
            L.service: 'alpine',
            L.command: 'echo',
            L.parent: '2',
            L.enter: '4'
        },
        '4': {
            L.method: 'execute',
            L.service: 'echo_helper',
            L.command: 'sonar',
            L.parent: '3'
        },
        '5': {
            L.method: 'execute',
            L.service: 'echo_helper',
            L.command: 'sonar',
            L.parent: '2'
        }
    }

    assert Services.resolve_chain(story, story.tree['1']) \
        == deque([Service(name='alpine'), Command(name='echo')])

    assert Services.resolve_chain(story, story.tree['2']) \
        == deque([Service(name='alpine'),
                  Command(name='echo'), Event(name='foo')])

    assert Services.resolve_chain(story, story.tree['3']) \
        == deque([Service(name='alpine'), Command(name='echo')])

    assert Services.resolve_chain(story, story.tree['4']) \
        == deque([Service(name='alpine'), Command(name='echo'),
                  Event(name='foo'), Command(name='sonar')])

    assert Services.resolve_chain(story, story.tree['5']) \
        == deque([Service(name='alpine'), Command(name='echo'),
                     Event(name='foo'), Command(name='sonar')])
