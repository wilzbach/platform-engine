# -*- coding: utf-8 -*-
import re

from asyncy.utils import Resolver

from pytest import mark

import storyscript


# def test_resolve_list():
#     data = {
#         'foo': 'bar',
#         'planets': ['mars', 'earth']
#     }
#     item = [
#         'hello',
#         {'$OBJECT': 'path', 'paths': ['foo']},
#         {'$OBJECT': 'path', 'paths': ['planets', '1']}
#     ]
#
#     assert Resolver.resolve(item, data) == 'hello bar earth'


@mark.parametrize('cases', [
    [{}, '"yoda"', 'yoda'],
    [{'planet': 'mars'}, 'planet', 'mars'],
    [{'planet': ['mars', 'earth']}, 'planet[0]', 'mars'],
    [{'planet': ['mars', 'earth']}, 'planet[1]', 'earth'],
    [{'planet': {'name': 'mars'}}, 'planet["name"]', 'mars'],
    [{'planet': {'name': 'mars'}}, 'planet["name__"]', None],
    [{'planet': 'mars'}, '{"planet": planet, "element": "air"}',
     {'planet': 'mars', 'element': 'air'}],
    [{}, '[0, 1, 2]', [0, 1, 2]],
    [{}, '/foo/', re.compile('/foo/')],
    [{}, '[true]', [True]],
])
def test_resolve_all_objects(cases):
    data = cases[0]
    statement = cases[1]
    expected_return = cases[2]

    tree = storyscript.Api.loads(f'a = {statement}')
    item = tree['tree']['1']['args'][0]

    assert Resolver.resolve(item, data) == expected_return
