# -*- coding: utf-8 -*-
import requests


class Http:

    @classmethod
    def _call(cls, method, url, json=False, **kwargs):
        request = getattr(requests, method)
        response = request(url, **kwargs)
        if json:
            return response.json()
        return response.text

    @classmethod
    def get(cls, url, json=False, **kwargs):
        return cls._call('get', url, json=json, **kwargs)

    @classmethod
    def post(cls, url, json=False, **kwargs):
        return cls._call('post', url, json=json, **kwargs)
