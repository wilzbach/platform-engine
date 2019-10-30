# -*- coding: utf-8 -*-
import asyncio
import urllib
from urllib.parse import urlencode

from tornado.httpclient import HTTPError


class HttpUtils:
    @staticmethod
    def read_response_body_quietly(response):
        try:
            return response.body.decode("utf-8")
        except BaseException:
            return None

    @staticmethod
    async def fetch_with_retry(tries, logger, url, http_client, kwargs):
        kwargs["raise_error"] = False

        # this makes it possible to override the default
        # retry_timeout
        retry_timeout = kwargs.get("retry_timeout", 0.5)

        if "retry_timeout" in kwargs:
            del kwargs["retry_timeout"]

        attempts = 0
        last_exception = None
        while attempts < tries:
            attempts = attempts + 1
            try:
                res = await http_client.fetch(url, **kwargs)
                if res.code == 599:  # Network connectivity issues.
                    raise HTTPError(
                        res.code, message=str(res.error), response=res
                    )
                return res
            except HTTPError as e:
                last_exception = e
                logger.error(
                    f"Failed to call {url}; attempt={attempts}; err={str(e)}"
                )
                await asyncio.sleep(retry_timeout)

        assert last_exception is not None  # Impossible.
        raise HTTPError(
            500, message=f"Failed to call {url}!"
        ) from last_exception

    @staticmethod
    def add_params_to_url(url, params: dict):
        if len(params) == 0:
            return url

        parts = []

        for key, value in params.items():
            key = urllib.parse.quote(key)
            if type(value) is list:
                for lv in value:
                    parts.append((key, str(lv)))
            else:
                parts.append((key, str(value)))

        return f"{url}?{urlencode(parts)}"
