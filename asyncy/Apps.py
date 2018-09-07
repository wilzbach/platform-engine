# -*- coding: utf-8 -*-
import json

import certifi
import psycopg2

from raven.contrib.tornado import AsyncSentryClient
from tornado.httpclient import AsyncHTTPClient

from .Sentry import Sentry
from .utils.HttpUtils import HttpUtils
from .Config import Config
from .Logger import Logger
from .App import App


class Apps:
    internal_services = ['http', 'log', 'crontab', 'file', 'event']
    apps = {}
    sentry_client = None

    @classmethod
    def _init_sentry(cls, sentry_dsn: str, release: str):
        cls.sentry_client = AsyncSentryClient(
            dsn=sentry_dsn,
            release=release
        )

    @classmethod
    def get_releases(cls):
        conn = psycopg2.connect(database='asyncy', user='postgres',
                                options=f'-c search_path=app_public')
        cur = conn.cursor()

        query = """
        with latest as (select app_uuid, max(id) as id 
            from releases group by app_uuid)
        select app_uuid, id, config, payload, maintenance
        from latest
            inner join releases using (app_uuid, id)
            inner join apps on (releases.app_uuid = apps.uuid);
        """
        cur.execute(query)

        return cur.fetchall()

    @classmethod
    async def init_all(cls, sentry_dsn: str, release: str,
                       config: Config, logger: Logger):
        cls._init_sentry(sentry_dsn, release)

        releases = cls.get_releases()

        for release in releases:
            app_id = release[0]
            version = release[1]
            environment = release[2]
            stories = release[3]
            maintenance = release[4]
            logger.info(f'Deploying app {app_id}@{version}')
            if maintenance:
                continue

            try:
                Sentry.clear_and_set_context(cls.sentry_client,
                                             app_id, version)

                services = await cls._prepare_services(
                    stories.get('yaml', {}), logger, stories)

                app = App(app_id, version, config, logger,
                          stories, services, environment,
                          sentry_client=cls.sentry_client)

                await app.bootstrap()

                cls.apps[app_id] = app
                logger.info(f'Successfully deployed app {app_id}@{version}')
            except BaseException as e:
                logger.error(
                    f'Failed to bootstrap app {app_id}@{version}', exc=e)
                cls.sentry_client.capture('raven.events.Exception')

    @classmethod
    def get(cls, app_id: str):
        return cls.apps[app_id]

    @classmethod
    async def _prepare_services(cls, asyncy_yaml, logger: Logger,
                                stories: dict):
        services = {}

        for service in stories.get('services', []):
            if service in cls.internal_services:
                continue

            conf = asyncy_yaml.get('services', {}).get(service, {})
            # query the Hub for the OMG
            tag = asyncy_yaml.get('tag', 'latest')
            if asyncy_yaml.get('image'):
                pull_url, omg = await cls.get_by_slug(logger, conf['image'],
                                                      tag)
            else:
                pull_url, omg = await cls.get_by_alias(logger, service, tag)

            image = f'{pull_url}:{tag}'
            omg['image'] = image

            services[service] = {
                'tag': tag,
                'configuration': omg
            }

        return services

    @classmethod
    async def get_by_alias(cls, logger, alias, tag):
        query = """
        query GetAlias($alias: Alias! $tag: String!){
          serviceByAlias(alias: $alias){
            pullUrl
            serviceTags(condition: {tag: $tag} first:1){
              nodes{
                configuration
              }
            }
          }
        }
        """

        client = AsyncHTTPClient()
        kwargs = {
            'headers': {'Content-Type': 'application/json'},
            'method': 'POST',
            'body': json.dumps({
                'query': query,
                'variables': {
                    'alias': alias,
                    'tag': tag
                }
            }),
            'ca_certs': certifi.where()
        }

        res = await HttpUtils.fetch_with_retry(
            3, logger, 'https://api.asyncy.com/graphql', client, kwargs)

        if res.code != 200:
            raise Exception(f'Failed to get config for {alias}:{tag}')

        graph_result = json.loads(res.body)

        res = graph_result['data']['serviceByAlias']
        assert res, 'Not found in Asyncy Hub'

        return (
            res['pullUrl'],
            res['serviceTags']['nodes'][0]['configuration']
        )

    @classmethod
    async def get_by_slug(cls, logger, image, tag):
        owner, repo = image.split('/')
        query = """
        query GetAlias($owner: Username! $repo: Username! $tag: String!){
          allOwners(condition: {username: $owner}, first: 1){
            nodes{
              repos(condition: {name: $repo}, first: 1){
                nodes{
                  services(first:1){
                    nodes{
                      pullUrl
                      serviceTags(condition: {tag: $tag}, first: 1){
                        nodes{
                         configuration
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        client = AsyncHTTPClient()

        kwargs = {
            'headers': {'Content-Type': 'application/json'},
            'method': 'POST',
            'body': json.dumps({
                'query': query,
                'variables': {
                    'owner': owner,
                    'repo': repo,
                    'tag': tag
                }
            }),
            'ca_certs': certifi.where()
        }

        res = await HttpUtils.fetch_with_retry(
            3, logger, 'https://api.asyncy.com/graphql', client, kwargs)

        if res.code != 200:
            raise Exception(f'Failed to get config for {image}:{tag}')

        graph_result = json.loads(res.body)
        res = graph_result['data']['allOwners'][0]['repos'][0]['services'][0]
        assert res, 'Not found in Asyncy Hub'

        return (
            res['pullUrl'],
            res['serviceTags']['nodes'][0]['configuration']
        )

    @classmethod
    async def destroy_app(cls, app: App):
        app.logger.info(f'Destroying app {app.app_id}')
        await app.destroy()
        app.logger.info(f'Completed destroying app {app.app_id}')
        cls.apps[app.app_id] = None

    @classmethod
    async def destroy_all(cls):
        for app in cls.apps.values():
            await cls.destroy_app(app)
