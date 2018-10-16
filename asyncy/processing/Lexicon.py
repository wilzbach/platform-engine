# -*- coding: utf-8 -*-
import json
import time
import urllib
import uuid
from urllib import parse

from tornado.httpclient import AsyncHTTPClient

from .Mutations import Mutations
from .Services import Services
from .. import Metrics
from ..Exceptions import AsyncyError
from ..Types import StreamingService
from ..constants.LineConstants import LineConstants
from ..constants.ServiceConstants import ServiceConstants
from ..utils import Dict
from ..utils.HttpUtils import HttpUtils


class Lexicon:
    """
    Lexicon of possible line actions and their implementation
    """

    @staticmethod
    async def execute(logger, story, line):
        """
        Runs a service with the resolution values as commands
        """
        service = line[LineConstants.service]

        start = time.time()

        if line.get('enter') is not None:
            """
            When a service to be executed has an 'enter' line number,
            it's a streaming service. Let's bring up the service and
            update the context with the output name.

            Example:
            foo stream as client
                when client grep:'bar' as result
                    # do something with result
            """
            output = await Services.start_container(story, line)
            Metrics.container_start_seconds_total.labels(
                app_id=story.app.app_id,
                story_name=story.name, service=service
            ).observe(time.time() - start)

            story.end_line(line['ln'], output=output,
                           assign={'paths': line.get('output')})

            return Lexicon.next_line_or_none(story.line(line.get('next')))
        else:
            output = await Services.execute(story, line)
            Metrics.container_exec_seconds_total.labels(
                app_id=story.app.app_id,
                story_name=story.name, service=service
            ).observe(time.time() - start)

            if line.get('name') and len(line['name']) == 1:
                story.end_line(line['ln'], output=output,
                               assign={'paths': line['name']})
            else:
                story.end_line(line['ln'], output=output,
                               assign=line.get('output'))

            return Lexicon.next_line_or_none(story.line(line.get('next')))

    @staticmethod
    async def function(logger, story, line):
        """
        Functions are not executed when they're encountered.
        This method returns the next block's line number,
        if there are more statements to be executed.
        """
        return Lexicon.next_line_or_none(story.next_block(line))

    @staticmethod
    def next_line_or_none(line):
        if line:
            return line['ln']

        return None

    @staticmethod
    async def set(logger, story, line):
        value = story.resolve(line['args'][0])

        if len(line['args']) > 1:
            # Check if args[1] is a mutation.
            if line['args'][1]['$OBJECT'] == 'mutation':
                value = Mutations.mutate(line['args'][1], value, story, line)
                logger.log_raw('debug', f'Mutation result: {value}')
            else:
                raise AsyncyError(
                    message=f'Unsupported argument in set: '
                            f'{line["args"][1]["$OBJECT"]}',
                    story=story, line=line)

        story.end_line(line['ln'], output=value,
                       assign={'$OBJECT': 'path', 'paths': line['name']})
        return Lexicon.next_line_or_none(story.line(line.get('next')))

    @staticmethod
    async def if_condition(logger, story, line):
        """
        Evaluates the resolution value to decide wheter to enter
        inside an if-block.
        """
        logger.log('lexicon-if', line, story.context)
        result = story.resolve(line['args'][0], encode=False)
        if result:
            return line['enter']
        return line['exit']

    @staticmethod
    def unless_condition(logger, story, line):
        logger.log('lexicon-unless', line, story.context)
        result = story.resolve(line['args'][0], encode=False)
        if result:
            return line['exit']
        return line['enter']

    @staticmethod
    async def for_loop(logger, story, line):
        """
        Evaluates a for loop
        """
        _list = story.resolve(line['args'][0], encode=False)
        output = line['output'][0]
        from . import Story
        for item in _list:
            story.context[output] = item
            await Story.execute_block(logger, story, line)
        return line['exit']

    @staticmethod
    async def when(logger, story, line):
        service = line[LineConstants.service]
        command = line[LineConstants.command]
        # Does this service belong to a streaming service?
        s = story.context.get(service)
        if isinstance(s, StreamingService):
            # Yes, we need to subscribe to an event with the service.
            conf = story.app.services[s.name][ServiceConstants.config]
            conf_event = Dict.find(
                conf, f'commands.{s.command}.events.{command}')

            port = Dict.find(conf_event, f'http.port', 80)
            subscribe_path = Dict.find(conf_event, 'http.subscribe.path')
            subscribe_method = Dict.find(conf_event,
                                         'http.subscribe.method', 'post')

            event_args = Dict.find(conf_event, 'arguments', {})

            data = {}
            for key in event_args:
                data[key] = story.argument_by_name(line, key)

            url = f'http://{s.hostname}:{port}{subscribe_path}'

            logger.debug(f'Sending subscription request to {url}')

            engine = f'{story.app.config.ENGINE_HOST}:' \
                     f'{story.app.config.ENGINE_PORT}'

            query_params = urllib.parse.urlencode({
                'story': story.name,
                'block': line['ln'],
                'app': story.app.app_id
            })

            sub_id = str(uuid.uuid4())

            body = {
                'endpoint': f'http://{engine}/story/event?{query_params}',
                'data': data,
                'event': command,
                'id': sub_id
            }

            kwargs = {
                'method': subscribe_method.upper(),
                'body': json.dumps(body),
                'headers': {
                    'Content-Type': 'application/json; charset=utf-8'
                }
            }

            client = AsyncHTTPClient()
            logger.debug(f'Subscribing to {service} from {s.command}...')

            response = await HttpUtils.fetch_with_retry(3, logger, url,
                                                        client, kwargs)
            if round(response.code / 100) == 2:
                logger.info(f'Subscribed!')
                story.app.add_subscription(sub_id, s, command, body)
                next_line = story.next_block(line)
                return Lexicon.next_line_or_none(next_line)
            else:
                raise AsyncyError(
                    message=f'Failed to subscribe to {service} from '
                            f'{s.command} in {s.container_name}! '
                            f'http err={response.error}; code={response.code}',
                    story=story, line=line)
        else:
            raise AsyncyError(message=f'Unknown service {service} for when!',
                              story=story, line=line)
