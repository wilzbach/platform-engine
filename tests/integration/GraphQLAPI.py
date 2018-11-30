# -*- coding: utf-8 -*-
from asyncy.GraphQLAPI import GraphQLAPI

from pytest import mark


@mark.asyncio
async def test_get_by_alias(logger):
    ret = await GraphQLAPI.get_by_alias(logger, 'http', 'latest')
    assert 'asyncy/http' in ret[0]
    assert ret[1]['omg'] is not None
    assert ret[1]['actions'] is not None


@mark.asyncio
async def test_get_by_slug(logger):
    ret = await GraphQLAPI.get_by_slug(logger, 'asyncy/http', 'latest')
    assert 'asyncy/http' in ret[0]
    assert ret[1]['omg'] is not None
    assert ret[1]['actions'] is not None
