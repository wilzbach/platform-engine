# -*- coding: utf-8 -*-
from asyncy.Exceptions import AsyncyError, TooManyActiveApps, \
    TooManyServices, TooManyVolumes

from pytest import raises


def test_asyncy_error():
    with raises(AsyncyError):
        raise AsyncyError('things happen')

# def test_asyncy_error_stack_trace(story):
#     with raises(AsyncyError):
#         story.name = 'trace.story'
#         story.tree = {
#             2: {'ln': 2},
#             3: {'ln': 3, 'parent': 2},
#             4: {'ln': 4, 'parent': 3}
#         }
#         raise AsyncyError('things happen and stack traces appear',
#                           story,
#                           story.line(4))

def test_many_volumes():
    with raises(TooManyVolumes):
        raise TooManyVolumes(10, 10)


def test_many_apps():
    with raises(TooManyActiveApps):
        raise TooManyActiveApps(10, 10)


def test_many_services():
    with raises(TooManyServices):
        raise TooManyServices(10, 10)
