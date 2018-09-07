# -*- coding: utf-8 -*-
import json

import certifi

from tornado.httpclient import AsyncHTTPClient

from .utils.HttpUtils import HttpUtils


class GraphQLAPI:

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
