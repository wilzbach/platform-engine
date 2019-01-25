# -*- coding: utf-8 -*-
import json
from collections import namedtuple

from requests.structures import CaseInsensitiveDict

from tornado.httpclient import AsyncHTTPClient

from .Config import Config
from .Logger import Logger
from .Types import StreamingService
from .constants.ServiceConstants import ServiceConstants
from .processing import Story
from .utils import Dict
from .utils.HttpUtils import HttpUtils

Subscription = namedtuple('Subscription',
                          ['streaming_service', 'id', 'payload', 'event'])


class App:

    def __init__(self, app_id: str, app_dns: str, version: int, config: Config,
                 logger: Logger, stories: dict, services: dict,
                 environment: dict):
        self._subscriptions = {}
        self.app_id = app_id
        self.app_dns = app_dns
        self.config = config
        self.version = version
        self.logger = logger
        if environment is None:
            environment = {}

        self.environment = CaseInsensitiveDict(data=environment)
        self.stories = stories['stories']
        self.entrypoint = stories['entrypoint']
        self.services = services
        secrets = CaseInsensitiveDict()
        for k, v in self.environment.items():
            if not isinstance(v, dict):
                secrets[k] = v
        self.app_context = {
            'secrets': secrets,
            'hostname': f'{self.app_dns}.asyncyapp.com',
            'version': self.version
        }

    async def bootstrap(self):
        """
        Executes all stories found in stories.json.
        This enables the story to listen to pub/sub,
        register with the gateway, and queue cron jobs.
        """
        await self.run_stories()

    async def run_stories(self):
        """
        Executes all the stories.
        This enables the story to listen to pub/sub,
        register with the gateway, and queue cron jobs.
        """
        for story_name in self.entrypoint:
            try:
                await Story.run(self, self.logger, story_name)
            except Exception as e:
                self.logger.error('Failed to bootstrap story', exc=e)
                raise e

    def add_subscription(self, sub_id: str,
                         streaming_service: StreamingService,
                         event: str, payload: dict):
        self._subscriptions[sub_id] = Subscription(streaming_service,
                                                   sub_id, payload, event)

    def get_subscription(self, sub_id: str):
        return self._subscriptions.get(sub_id)

    def remove_subscription(self, sub_id: str):
        self._subscriptions.pop(sub_id)

    async def clear_subscriptions_synapse(self):
        url = f'http://{self.config.ASYNCY_SYNAPSE_HOST}:' \
              f'{self.config.ASYNCY_SYNAPSE_PORT}/clear_all'
        kwargs = {
            'method': 'POST',
            'body': json.dumps({
                'app_id': self.app_id
            }),
            'headers': {
                'Content-Type': 'application/json; charset=utf-8'
            }
        }
        client = AsyncHTTPClient()
        response = await HttpUtils.fetch_with_retry(3, self.logger, url,
                                                    client, kwargs)
        if int(response.code / 100) == 2:
            self.logger.debug(f'Unsubscribed all with Synapse!')
            return True
        else:
            self.logger.error(f'Failed to unsubscribe with Synapse!')
            return False

    async def unsubscribe_all(self):
        for sub_id, sub in self._subscriptions.items():
            assert isinstance(sub, Subscription)
            assert isinstance(sub.streaming_service, StreamingService)
            conf = Dict.find(
                self.services, f'{sub.streaming_service.name}'
                               f'.{ServiceConstants.config}'
                               f'.actions.{sub.streaming_service.command}'
                               f'.events.{sub.event}.http')

            http_conf = conf.get('unsubscribe')
            if not http_conf:
                self.logger.debug(f'No unsubscribe call required for {sub}')
                continue

            url = f'http://{sub.streaming_service.hostname}' \
                  f':{http_conf.get("port", conf.get("port", 80))}' \
                  f'{http_conf["path"]}'

            client = AsyncHTTPClient()
            self.logger.info(f'Unsubscribing {sub}...')

            method = http_conf.get('method', 'post')

            kwargs = {
                'method': method.upper(),
                'body': json.dumps(sub.payload['sub_body']),
                'headers': {
                    'Content-Type': 'application/json; charset=utf-8'
                }
            }

            response = await HttpUtils.fetch_with_retry(3, self.logger, url,
                                                        client, kwargs)
            if int(response.code / 100) == 2:
                self.logger.debug(f'Unsubscribed!')
            else:
                self.logger.error(f'Failed to unsubscribe {sub}!')

    async def destroy(self):
        """
        Unsubscribe from all existing subscriptions,
        and delete the namespace.
        """
        await self.clear_subscriptions_synapse()
        await self.unsubscribe_all()
