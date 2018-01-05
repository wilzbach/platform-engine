# -*- coding: utf-8 -*-
import base64

import requests


class Http:

    @staticmethod
    def get(url, transform=None):
        response = requests.get(url)
        response.raise_for_status()

        if transform == 'base64':
            return base64.b64decode(response.text)
        elif transform == 'json':
            return response.json()
        return response.text
