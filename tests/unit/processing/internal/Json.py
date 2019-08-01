# -*- coding: utf-8 -*-
from pytest import mark

from storyruntime.processing.internal import Json


@mark.asyncio
async def test_stringify():
    assert await Json.stringify(None, None, {'content': {'foo': 'bar'}}) \
        == '{"foo": "bar"}'


@mark.asyncio
async def test_parse():
    assert await Json.parse(None, None, {'content': '{"foo": "bar"}'}) \
        == {'foo': 'bar'}
