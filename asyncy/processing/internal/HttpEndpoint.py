# -*- coding: utf-8 -*-
from ...Exceptions import InvalidCommandError


class HttpEndpoint:
    @classmethod
    def run(cls, story, line):
        container = line['container']

        if container is 'request':
            return HttpEndpoint.access_request(story, line)
        elif container is 'response':
            return HttpEndpoint.access_response(story, line)
        else:
            raise NotImplementedError('Unknown method - ' + container)

    @classmethod
    def access_request(cls, story, line):
        # todo: Hack - read the command until we have a field in the tree
        # dedicated for the command.
        command = line['args'][0]['paths'][0]
        # TODO 16/05/2018: implement the below by
        # accessing story.context.__server_request__
        if command is 'set_status':
            pass
        elif command is 'set_header':
            pass
        elif command is 'write':
            pass
        elif command is 'finish':
            pass
        else:
            raise InvalidCommandError(command)
        pass

    @classmethod
    def access_response(cls, story, line):
        # todo: Hack - read the command until we have a field in the tree
        # dedicated for the command.
        command = line['args'][0]['paths'][0]
        # TODO 16/05/2018: implement the below by
        # accessing story.context.__server_request__
        if command is 'set_status':
            pass
        elif command is 'set_header':
            pass
        elif command is 'write':
            pass
        elif command is 'finish':
            pass
        else:
            raise InvalidCommandError(command)

    @classmethod
    def register_http_endpoint(cls, story_name, method, path, parent_line):
        # TODO 09/05/2018: Make an rpc call to the server.
        pass
