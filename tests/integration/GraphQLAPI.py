# -*- coding: utf-8 -*-
from asyncy.GraphQLAPI import GraphQLAPI

from pytest import mark


@mark.asyncio
async def test_get_by_alias(logger):
    ret = await GraphQLAPI.get_by_alias(logger, 'slack', 'latest')
    assert ret[0] == 'microservices/slack'
    assert ret[1]['version'] is not None
    assert ret[1]['commands'] is not None


@mark.asyncio
async def test_get_by_slug(logger):
    ret = await GraphQLAPI.get_by_slug(logger, 'judepereira/lastfm', 'latest')
    assert ret[0] == 'https://registry.hub.docker.com/judepereira/lastfm'
    assert ret[1]['commands'] is not None
