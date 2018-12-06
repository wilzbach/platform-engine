# -*- coding: utf-8 -*-
import asyncio
import urllib
from urllib import parse

from tornado.httpclient import HTTPError


class HttpUtils:

    @staticmethod
    async def fetch_with_retry(tries, logger, url, http_client, kwargs):
        kwargs['raise_error'] = False
        attempts = 0
        last_exception = None
        while attempts < tries:
            attempts = attempts + 1
            try:
                res = await http_client.fetch(url, **kwargs)
                if res.code == 599:  # Network connectivity issues.
                    raise HTTPError(res.code, message=str(res.error),
                                    response=res)
                return res
            except HTTPError as e:
                last_exception = e
                logger.log_raw(
                    'error',
                    f'Failed to call {url}; attempt={attempts}; err={str(e)}'
                )
                await asyncio.sleep(0.5)

        assert last_exception is not None  # Impossible.
        raise HTTPError(500, message=f'Failed to call {url}!') \
            from last_exception

    @staticmethod
    def add_params_to_url(url, params):
        return f'{url}?{urllib.parse.urlencode(params)}'
