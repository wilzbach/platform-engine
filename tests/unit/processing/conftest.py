# -*- coding: utf-8 -*-
from pytest import fixture


@fixture
def http_line():
    return {
        'ln': '1',
        'container': 'http-endpoint',
        'next': '2',
        'method': 'run',
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
