# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from asyncy.utils.HttpUtils import HttpUtils

import pytest
from pytest import mark

from tornado.httpclient import HTTPError


@mark.asyncio
async def test_fetch_with_retry(patch, logger, async_mock):
    client = MagicMock()

    patch.object(client, 'fetch', new=async_mock())
    kwargs = {
        'foo': 'bar'
    }
    ret = await HttpUtils.fetch_with_retry(3, logger, 'asyncy.com', client,
                                           kwargs)

    assert ret == client.fetch.mock.return_value
    client.fetch.mock.assert_called_with('asyncy.com', foo='bar',
                                         raise_error=False)


@mark.asyncio
async def test_fetch_with_retry_fail(patch, logger):
    client = MagicMock()
    fetch = MagicMock()

    async def exc(*args, **kwargs):
        fetch(*args, **kwargs)
        res = MagicMock()
        res.code = 599
        return res

    patch.object(client, 'fetch', side_effect=exc)

    with pytest.raises(HTTPError):
        await HttpUtils.fetch_with_retry(10, logger, 'asyncy.com', client, {})

    assert len(fetch.mock_calls) == 10
