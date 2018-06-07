# -*- coding: utf-8 -*-
from tornado.httpclient import HTTPError


class HttpUtils:

    @staticmethod
    async def fetch_with_retry(tries, logger, url, http_client, kwargs):
        attempts = 0
        while attempts < tries:
            attempts = attempts + 1
            try:
                return await http_client.fetch(url, **kwargs)
            except HTTPError as e:
                logger.log_raw(
                    'error',
                    f'Failed to call {url}; attempt={attempts}; err={str(e)}'
                )

        raise HTTPError(500, message=f'Failed to call {url}!')
