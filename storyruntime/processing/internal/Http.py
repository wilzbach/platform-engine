# -*- coding: utf-8 -*-
import cgi
import json

import certifi

from tornado.httpclient import AsyncHTTPClient

from .Decorators import Decorators
from ...Exceptions import StoryscriptError
from ...utils.HttpUtils import HttpUtils


@Decorators.create_service(name='http', command='fetch', arguments={
    'url': {'type': 'string'},
    'headers': {'type': 'map'},
    'body': {'type': 'string'},
    'method': {'type': 'string'}
}, output_type='any')
async def http_post(story, line, resolved_args):
    method = resolved_args.get('method', 'get') or 'get'
    http_client = AsyncHTTPClient()
    kwargs = {'method': method.upper(), 'ca_certs': certifi.where()}

    headers = resolved_args.get('headers') or {}
    if headers.get('User-Agent') is None:
        headers['User-Agent'] = 'Storyscript/1.0-beta'

    kwargs['headers'] = headers

    if resolved_args.get('body'):
        kwargs['body'] = resolved_args['body']
        if isinstance(kwargs['body'], dict):
            kwargs['body'] = json.dumps(kwargs['body'])

    response = await HttpUtils.fetch_with_retry(3, story.logger,
                                                resolved_args['url'],
                                                http_client, kwargs)

    charset = 'utf-8'

    content_type = response.headers.get('Content-Type')
    if content_type is not None and \
            'charset' in content_type:
        parsed = cgi.parse_header(content_type)

        if len(parsed) > 1:
            charset = parsed[1].get('charset')

    if int(response.code / 100) != 2:
        # Attempt to read the response body.
        response_body = None
        try:
            response_body = response.body.decode(charset)
        except UnicodeDecodeError:
            pass

        raise StoryscriptError(
            story=story,
            line=line,
            message=f'Failed to make HTTP call: {response.error}; '
            f'response code={response.code}; response body={response_body}')

    if 'application/json' in response.headers.get('Content-Type'):
        try:
            return json.loads(response.body.decode(charset))
        except json.decoder.JSONDecodeError:
            story.logger.warn(
                f'Failed to parse response as JSON, '
                f'although application/json was specified! '
                f'response={response.body.decode(charset)}')

    return response.body.decode(charset)


def init():
    pass
