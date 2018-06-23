# -*- coding: utf-8 -*-
from tornado.httpclient import AsyncHTTPClient

from .Decorators import Decorators
from ...utils.HttpUtils import HttpUtils


@Decorators.create_service(name='http', command='post', arguments={
    'url': {'type': 'string'},
    'headers': {'type': 'map'},
    'body': {'type': 'string'}
}, output_type='any')
async def http_post(story, line, resolved_args):
    http_client = AsyncHTTPClient()
    kwargs = _make_kwargs('POST', resolved_args.get('headers'))

    if resolved_args.get('body'):
        kwargs['body'] = resolved_args['body']

    return await HttpUtils.fetch_with_retry(1, story.logger,
                                            resolved_args['url'],
                                            http_client, kwargs)


@Decorators.create_service(name='http', command='get', arguments={
    'url': {'type': 'string'},
    'headers': {'type': 'map'}
}, output_type='any')
async def http_get(story, line, resolved_args):
    http_client = AsyncHTTPClient()
    kwargs = _make_kwargs('GET', resolved_args.get('headers'))

    return await HttpUtils.fetch_with_retry(1, story.logger,
                                            resolved_args['url'],
                                            http_client, kwargs)


def _make_kwargs(method, headers):
    kwargs = {'method': method}
    if headers:
        kwargs['headers'] = headers

    return kwargs


def init():
    pass
