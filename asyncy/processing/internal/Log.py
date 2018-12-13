# -*- coding: utf-8 -*-
from .Decorators import Decorators


@Decorators.create_service(name='log', command='info', arguments={
    'msg': {'type': 'any'}
})
async def info(story, line, resolved_args):
    story.app.logger.info(f'{story.name}: {resolved_args["msg"]}')


@Decorators.create_service(name='log', command='error', arguments={
    'msg': {'type': 'any'}
})
async def error(story, line, resolved_args):
    story.app.logger.error(f'{story.name}: {resolved_args["msg"]}')


@Decorators.create_service(name='log', command='warn', arguments={
    'msg': {'type': 'any'}
})
async def warn(story, line, resolved_args):
    story.app.logger.warn(f'{story.name}: {resolved_args["msg"]}')


@Decorators.create_service(name='log', command='debug', arguments={
    'msg': {'type': 'any'}
})
async def debug(story, line, resolved_args):
    story.app.logger.debug(f'{story.name}: {resolved_args["msg"]}')


def init():
    pass
