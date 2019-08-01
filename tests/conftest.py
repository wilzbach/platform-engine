# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from pytest import fixture

from storyruntime.constants.LineConstants import LineConstants
from storyruntime.constants.ServiceConstants import ServiceConstants


@fixture
def magic(mocker):
    """
    Shorthand for mocker.MagicMock. It's magic!
    """
    return mocker.MagicMock


@fixture
def async_cm_mock(magic):
    class AsyncContextManagerMock(MagicMock):
        async def __aenter__(self):
            return self.aenter

        async def __aexit__(self, *args):
            pass
    return AsyncContextManagerMock(magic)


@fixture
def async_mock():

    def return_value(*args, **kwargs):
        """
        Inspired from
        https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code.
        """
        m = MagicMock(*args, **kwargs)

        async def mock_coro(*args, **kwargs):
            return m(*args, **kwargs)

        mock_coro.mock = m
        return mock_coro

    return return_value


@fixture
def patch_init(mocker):
    """
    Makes patching a class' constructor slightly easier
    """
    def patch_init(item):
        mocker.patch.object(item, '__init__', return_value=None)
    return patch_init


@fixture
def patch_many(mocker):
    """
    Makes patching many attributes of the same object simpler
    """
    def patch_many(item, attributes):
        for attribute in attributes:
            mocker.patch.object(item, attribute)
    return patch_many


@fixture
def patch(mocker, patch_init, patch_many):
    mocker.patch.init = patch_init
    mocker.patch.many = patch_many
    return mocker.patch


@fixture
def echo_line():
    return {
        'ln': '1',
        LineConstants.service: 'alpine',
        LineConstants.command: 'echo',
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'msg',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'foo'
                }
            }
        ]
    }


@fixture
def echo_service():
    return {
        'alpine': {
            ServiceConstants.config: {
                'lifecycle': {
                    'startup': {
                        'command': ['tail', '-f', '/dev/null']
                    }
                },
                'actions': {
                    'echo': {
                        'arguments': {
                            'msg': {
                                'type': 'string'
                            }
                        }
                    }
                }
            }
        }
    }
