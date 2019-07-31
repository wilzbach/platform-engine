# -*- coding: utf-8 -*-
import pytest
from pytest import mark

from storyruntime.Exceptions import ServiceNotFound
from storyruntime.GraphQLAPI import GraphQLAPI


@mark.asyncio
async def test_get_by_alias(logger):
    ret = await GraphQLAPI.get_by_alias(logger, 'http', 'latest')
    assert 'asyncy/http' in ret[1]
    assert ret[2]['omg'] is not None
    assert ret[2]['actions'] is not None


@mark.asyncio
async def test_get_by_alias_invalid(logger):
    with pytest.raises(ServiceNotFound):
        await GraphQLAPI.get_by_alias(
            logger, 'this_alias_better_not_exist___', 'latest')


@mark.asyncio
async def test_get_by_slug(logger):
    ret = await GraphQLAPI.get_by_slug(logger, 'storyscript/http', 'latest')
    assert 'asyncy/http' in ret[1]
    assert ret[2]['omg'] is not None
    assert ret[2]['actions'] is not None


@mark.asyncio
async def test_get_by_slug_invalid_owner(logger):
    with pytest.raises(ServiceNotFound):
        await GraphQLAPI.get_by_slug(
            logger, 'this_owner_better_not_exist___/http', 'latest')


@mark.asyncio
async def test_get_by_slug_invalid_service(logger):
    with pytest.raises(ServiceNotFound):
        await GraphQLAPI.get_by_slug(
            logger, 'asyncy/this_service_better_not_exist___', 'latest')
