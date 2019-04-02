# -*- coding: utf-8 -*-
import typing
from collections import namedtuple

Expose = namedtuple('Expose',
                    ['name', 'service', 'service_expose_name', 'http_path'])

KEY_EXPOSE = 'expose'


class AppConfig:
    _expose: typing.List[Expose] = []

    def __init__(self, raw: dict):
        for name, expose in raw.get(KEY_EXPOSE, {}):
            e = Expose(name=name, service=expose.get('service'),
                       service_expose_name=expose.get('name'),
                       http_path=expose.get('http', {}).get('path'))

            assert e.name is not None
            assert e.service is not None
            assert e.service_expose_name is not None
            assert e.http_path is not None
            self._expose.append(e)

    def get_expose_config(self):
        return self._expose
