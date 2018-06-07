# -*- coding: utf-8 -*-
from pytest import fixture

from asyncy.constants.LineConstants import LineConstants


@fixture
def http_line():
    return {
        'ln': '1',
        LineConstants.service: 'http-endpoint',
        'next': '2',
        'method': 'execute',
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'method',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'get'
                }
            },
            {
                '$OBJECT': 'argument',
                'name': 'path',
                'argument': {
                    '$OBJECT': 'string',
                    'string': '/foo'
                }
            }
        ]
    }
