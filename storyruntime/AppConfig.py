# -*- coding: utf-8 -*-
import typing
from collections import namedtuple

from .utils.Dict import Dict

Forward = namedtuple('Forward',
                     ['service', 'service_forward_name', 'http_path'])

KEY_EXPOSE = 'expose'
"""This is deprecated. It was the previous key for forwards."""

KEY_FORWARDS = 'forwards'


class AppConfig:
    _expose: typing.List[Forward] = None

    def __init__(self, raw: dict):
        self._expose = []
        for expose in raw.get(KEY_FORWARDS, raw.get(KEY_EXPOSE, [])):
            e = Forward(service=expose.get('service'),
                        service_forward_name=expose.get('name'),
                        http_path=Dict.find(expose, 'http.path'))

            assert e.service is not None
            assert e.service_forward_name is not None
            assert e.http_path is not None
            self._expose.append(e)

    def get_expose_config(self):
        return self._expose
