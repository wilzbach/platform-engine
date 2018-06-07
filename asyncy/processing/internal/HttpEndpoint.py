# -*- coding: utf-8 -*-
from tornado.httpclient import AsyncHTTPClient, HTTPError

import ujson

from ...constants.LineConstants import LineConstants
from ...Exceptions import AsyncyError, InvalidCommandError
from ...constants.ContextConstants import ContextConstants
from ...utils.HttpUtils import HttpUtils


class HttpEndpoint:
    @classmethod
    def run(cls, story, line):
        container = line[LineConstants.service]

        if container == 'request':
            return HttpEndpoint.access_request(story, line)
        elif container == 'response':
            return HttpEndpoint.access_response(story, line)
        else:
            raise NotImplementedError('Unknown method - ' + container)

    @classmethod
    def access_request(cls, story, line):
        # todo: Hack - read the command until we have a field in the tree
        # dedicated for the command.
        command = line['args'][0]['paths'][0]
        req = story.context[ContextConstants.server_request]
        # TODO 19/05/2018: This is not implemented fully due to unknown specs.
        if command == 'body':
            return req.body
        else:
            raise InvalidCommandError(command, story=story, line=line)

    @classmethod
    def access_response(cls, story, line):
        # todo: Hack - read the command until we have a field in the tree
        # dedicated for the command.
        command = line['args'][0]['paths'][0]
        req = story.context[ContextConstants.server_request]

        data = {
            'command': command
        }

        if command == 'set_status':
            data['code'] = story.argument_by_name(line, 'code')
        elif command == 'set_header':
            data['key'] = story.argument_by_name(line, 'key')
            data['value'] = story.argument_by_name(line, 'value')
        elif command == 'write':
            data['content'] = story.argument_by_name(line, 'content')
        elif command == 'finish':
            # Do nothing.
            pass
        else:
            raise InvalidCommandError(command, story=story, line=line)

        story.context[ContextConstants.server_io_loop].add_callback(
            lambda: req.write(ujson.dumps(data) + '\n'))

        if command == 'finish':
            story.context[ContextConstants.server_io_loop]\
                .add_callback(req.finish)

    @classmethod
    async def register_http_endpoint(cls, story, line, method, path, block):
        await cls._update_gateway(story, line, method,
                                  'register', path, block)

    @classmethod
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
