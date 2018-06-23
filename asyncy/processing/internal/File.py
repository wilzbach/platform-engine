# -*- coding: utf-8 -*-
import os

from .Decorators import Decorators
from ...Exceptions import AsyncyError


@Decorators.create_service(name='file', command='write', arguments={
    'path': {'type': 'string'},
    'content': {'type': 'any'}
})
async def file_write(story, line, resolved_args):
    # TODO handle /asyncy/story.hash here
    try:
        with open(resolved_args['path'], 'w') as f:
            f.write(resolved_args['content'])
    except IOError as e:
        raise AsyncyError(message=f'Failed to write to file: {e}',
                          story=story, line=line)


@Decorators.create_service(name='file', command='read', arguments={
    'path': {'type': 'string'}
}, output_type='string')
async def file_read(story, line, resolved_args):
    # TODO handle /asyncy/story.hash here
    try:
        with open(resolved_args['path'], 'r') as f:
            return f.read()
    except IOError as e:
        raise AsyncyError(message=f'Failed to read file: {e}',
                          story=story, line=line)


@Decorators.create_service(name='file', command='exists', arguments={
    'path': {'type': 'string'}
}, output_type='boolean')
async def file_exists(story, line, resolved_args):
    # TODO handle /asyncy/story.hash here
    return os.path.exists(resolved_args['path'])


def init():
    pass
