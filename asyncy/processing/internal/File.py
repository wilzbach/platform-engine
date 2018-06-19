# -*- coding: utf-8 -*-
from .Decorators import Decorators


@Decorators.create_service(name='file', command='write', arguments={
    'path': {'type': 'string'},
    'content': {'type': 'any'}
})
def file_write(story, line, resolved_args):
    pass


@Decorators.create_service(name='file', command='read', arguments={
    'path': {'type': 'string'}
}, output_type='string')
def file_read(story, line, resolved_args):
    pass


@Decorators.create_service(name='file', command='exists', arguments={
    'path': {'type': 'string'}
}, output_type='boolean')
def file_exists(story, line, resolved_args):
    pass


def init():
    pass
