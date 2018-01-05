# -*- coding: utf-8 -*-
import base64

import requests


class Http:

    @staticmethod
    def _transform(response, transformation):
        if transformation == 'base64':
            return base64.b64decode(response.text)
        elif transformation == 'json':
            return response.json()
        return response.text

    @classmethod
    def get(cls, url, transformation=None):
        response = requests.get(url)
        response.raise_for_status()
        return cls._transform(response, transformation)

    @classmethod
    def post(cls, url, transformation=None):
        response = requests.post(url)
        response.raise_for_status()
        return cls._transform(response, transformation)
