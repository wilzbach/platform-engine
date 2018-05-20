# -*- coding: utf-8 -*-

from tornado import httpclient
from tornado.httpclient import HTTPRequest

import ujson

from ...Exceptions import AsyncyError, InvalidCommandError
from ...constants.ContextConstants import ContextConstants


class HttpEndpoint:
    @classmethod
    def run(cls, story, line):
        container = line['container']

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
            raise InvalidCommandError(command)
        pass

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
            raise InvalidCommandError(command)

        req.write(ujson.dumps(data) + '\n')

        if command == 'finish':
            req.finish()

    @classmethod
    def register_http_endpoint(cls, story, method, path, line):
        url = 'http://{}/register/story'
        url = url.format(story.app.config.gateway_url)

        req = HTTPRequest(
            url=url,
            method='POST',
            headers={
                'Content-Type': 'application/json; charset=utf-8'
            },
            body=ujson.dumps({
                'method': method,
                'endpoint': path,
                'story_name': story.name,
                'line': line
            })
        )

        tries = 3

        while tries > 0:
            tries = tries - 1

            http_client = httpclient.HTTPClient()

            try:
                http_client.fetch(req)
                story.logger.log_raw(
                    'info',
                    'Registered successfully with the gateway')
                return
            except httpclient.HTTPError as e:
                # HTTPError is raised for non-200 responses; the response
                # can be found in e.response.
                story.logger.log_raw(
                    'error', 'The gateway sent a non 200 status; body=' +
                             e.response.body)
            except Exception as e:
                # Other errors are possible, such as IOError.
                story.logger.log_raw('error', 'Is the gateway up?' + str(e))
            finally:
                http_client.close()

        msg = 'Exhausted all retries while ' \
              'attempting to register story ' \
              + story.name + ' with the gateway'

        story.logger.log_raw('error', msg)
        raise AsyncyError(message=msg)
