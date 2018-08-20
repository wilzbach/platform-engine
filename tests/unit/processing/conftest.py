# -*- coding: utf-8 -*-
from asyncy.constants.LineConstants import LineConstants

from pytest import fixture


@fixture
def http_line():
    return {
        'ln': '1',
        LineConstants.service: 'http-endpoint',
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
