# -*- coding: utf-8 -*-
from asyncy.processing.internal import Json

from pytest import mark


@mark.asyncio
async def test_stringify():
    assert await Json.stringify(None, None, {'content': {'foo': 'bar'}}) \
        == '{"foo": "bar"}'


@mark.asyncio
async def test_parse():
    assert await Json.parse(None, None, {'content': '{"foo": "bar"}'}) \
        == {'foo': 'bar'}
