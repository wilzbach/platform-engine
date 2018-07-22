# -*- coding: utf-8 -*-
from tornado.httpclient import AsyncHTTPClient, HTTPError

import ujson

from ... import Metrics
from ...Exceptions import AsyncyError, InvalidCommandError
from ...constants.ContextConstants import ContextConstants
from ...constants.LineConstants import LineConstants
from ...utils.HttpUtils import HttpUtils


class HttpEndpoint:
    @classmethod
    def run(cls, story, line):
        req = story.context[ContextConstants.server_request]

        command = line['command']

        data = {
            'command': command
        }

        gateway_request = story.context[ContextConstants.gateway_request]

        if command == 'body':
            return gateway_request['json_context']['request']['body']
        elif command == 'get_header':
            key = story.argument_by_name(line, 'key')
            return gateway_request['json_context']['request']['headers'] \
                .get(key)
        elif command == 'set_status':
            data['code'] = story.argument_by_name(line, 'code')
        elif command == 'set_header':
            data['key'] = story.argument_by_name(line, 'key')
            data['value'] = story.argument_by_name(line, 'value')
        elif command == 'write':
            if story.argument_by_name(line, 'content') is None:
                story.logger.log_raw('warn', 'Attempt to call http/write:'
                                             'content with content as None!')
                return
            data['content'] = story.argument_by_name(line, 'content')
        elif command == 'finish':
            # Do nothing.
            pass
        else:
            raise InvalidCommandError(command, story=story, line=line)

        io_loop = story.context[ContextConstants.server_io_loop]
        io_loop.add_callback(lambda: req.write(ujson.dumps(data) + '\n'))

        if command == 'finish':
            io_loop.add_callback(req.finish)

    @classmethod
    @Metrics.http_register.time()
    async def register_http_endpoint(cls, story, line, method, path, block):
        await cls._update_gateway(story, line, method,
                                  'register', path, block)

    @classmethod
    @Metrics.http_unregister.time()
    async def unregister_http_endpoint(cls, story, line, method, path, block):
        await cls._update_gateway(story, line, method,
                                  'unregister', path, block)

    @classmethod
    async def _update_gateway(cls, story, line, method, action, path, block):
        url = f'http://{story.app.config.gateway_url}/{action}'

        body = ujson.dumps({
            'method': method,
            'endpoint': path,
            'filename': story.name,
            'block': block
        })

        kwargs = {
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json; charset=utf-8'
            },
            'body': body
        }

        http_client = AsyncHTTPClient()

        try:
            await HttpUtils.fetch_with_retry(3, story.logger,
                                             url, http_client, kwargs)
        except HTTPError as e:
            story.logger.log_raw('error', 'Is the gateway up?' + str(e))
            msg = 'Exhausted all retries while ' \
                  'attempting to register story ' \
                  + story.name + ' with the gateway'

            story.logger.log_raw('error', msg)
            raise AsyncyError(message=msg, story=story, line=line)
