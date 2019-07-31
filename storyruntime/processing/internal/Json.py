# -*- coding: utf-8 -*-
import json

from .Decorators import Decorators


@Decorators.create_service(name='json', command='stringify', arguments={
    'content': {'type': 'string'}
}, output_type='any')
async def stringify(story, line, resolved_args):
    return json.dumps(resolved_args['content'])


@Decorators.create_service(name='json', command='parse', arguments={
    'content': {'type': 'string'}
}, output_type='any')
async def parse(story, line, resolved_args):
    return json.loads(resolved_args['content'])


def init():
    pass
