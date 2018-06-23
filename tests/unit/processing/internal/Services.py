# -*- coding: utf-8 -*-
from asyncy.Exceptions import AsyncyError
from asyncy.constants.LineConstants import LineConstants
from asyncy.processing.internal.Services import Services

import pytest
from pytest import mark


@mark.asyncio
async def test_services_execute(story, async_mock):
    handler = async_mock(return_value='output')

    Services.register('my_service', 'my_command', {}, 'any', handler)

    assert Services.is_internal('my_service') is True
    line = {
        LineConstants.service: 'my_service',
        'command': 'my_command'
    }

    assert await Services.execute(story, line) == 'output'


@mark.asyncio
async def test_services_execute_invalid_command(story):
    Services.register('my_service', 'my_command', {}, 'any', None)

    line = {
        LineConstants.service: 'my_service',
        'command': 'foo_command'
    }

    with pytest.raises(AsyncyError):
        await Services.execute(story, line)


@mark.asyncio
async def test_services_execute_args(story, async_mock):
    handler = async_mock(return_value='output')

    Services.register('my_service', 'my_command',
                      {'arg1': {'type': 'string'}},
                      'any', handler)

    assert Services.is_internal('my_service') is True
    line = {
        LineConstants.service: 'my_service',
        'command': 'my_command',
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
    Services.register('my_service', 'my_command', {}, 'any', None)
    Services.log_registry()
    logger.log_raw.assert_called_with(
        'info', 'Discovered internal service my_service/my_command')
