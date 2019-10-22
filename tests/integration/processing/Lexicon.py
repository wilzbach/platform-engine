# -*- coding: utf-8 -*-
import re

from pytest import mark

from storyruntime.Exceptions import StackOverflowException, StoryscriptError, \
    StoryscriptRuntimeError, TypeAssertionRuntimeError, TypeValueRuntimeError

from tests.integration.processing.Entities import Case, Suite

from .Assertions import ContextAssertion, ListItemAssertion, \
    MapValueAssertion, RuntimeExceptionAssertion


@mark.parametrize('suite', [
    Suite(preparation_lines='a = [20, 12, 23]', cases=[
        Case(append='a[0] = 100', assertion=ContextAssertion(
            key='a', expected=[100, 12, 23]))
    ]),

    Suite(preparation_lines='a = [[20, 12, 23], [-1]]', cases=[
        Case(append='a[0][1] = 100\na[1][0] = 10',
             assertion=ContextAssertion(
                 key='a', expected=[[20, 100, 23], [10]]))
    ])
])
@mark.asyncio
async def test_arrays(suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        preparation_lines='a = 2 + 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=4))
        ]
    ),
    Suite(
        preparation_lines='a = 0 + 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=2))
        ]
    ),
    Suite(
        preparation_lines='a = 2 - 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=0))
        ]
    ),
    Suite(
        preparation_lines='a = 2 / 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=1))
        ]
    ),
    Suite(
        preparation_lines='a = "a" + "b"',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected='ab'))
        ]
    ),
    Suite(
        preparation_lines='a = "a" + "b" + ("c" + "d")',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected='abcd'))
        ]
    ),
    Suite(
        preparation_lines='a = 2 + 10 / 5',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=4))
        ]
    ),
    Suite(
        preparation_lines='a = 20 * 100',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=2000))
        ]
    ),
    Suite(
        preparation_lines='a = 10 % 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=0))
        ]
    ),
    Suite(
        preparation_lines='a = 11 % 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=1))
        ]
    ),
    Suite(
        preparation_lines='a = 2.5 ^ 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=6.25))
        ]
    ),
    Suite(
        preparation_lines='a = 20 / 1000',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=0.02))
        ]
    ),
    Suite(
        preparation_lines='a = 2 * 4 / 4',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=2))
        ]
    ),
    Suite(
        preparation_lines='a = 2 * 4 / (4 * 2)',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=1))
        ]
    ),
    Suite(
        preparation_lines='a = 2 * 4 / (4 * 2) + 1',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=2))
        ]
    ),
    Suite(
        preparation_lines='a = 2 * 4 / (4 * 2) + 1 * 20',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=21))
        ]
    ),
    Suite(
        preparation_lines='a = [1, 2, 3]\n'
                          'b = [3, 4, 5]\n'
                          'c = a + b',
        cases=[
            Case(
                assertion=ContextAssertion(key='c',
                                           expected=[1, 2, 3, 3, 4, 5])
            )
        ]
    ),
    Suite(
        preparation_lines='foo = 2\n'
                          'zero = 0\n'
                          'a = 2 * 4 / (4 * foo) + 1 * 20 + zero',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=21))
        ]
    ),
    Suite(
        preparation_lines='a = {} to Map[any,int]\n',
        cases=[
            Case(append='a["b"] = 1',
                 assertion=MapValueAssertion(key='a',
                                             map_key='b',
                                             expected=1)),
            Case(append='a[0] = 2',
                 assertion=MapValueAssertion(key='a',
                                             map_key=0,
                                             expected=2)),
            Case(append='a[0.5] = 3',
                 assertion=MapValueAssertion(key='a',
                                             map_key=0.5,
                                             expected=3)),
            Case(append='b = "key"\n'
                        'a[b] = 4',
                 assertion=MapValueAssertion(key='a',
                                             map_key='key',
                                             expected=4))
        ]
    ),
    Suite(
        preparation_lines='a = [1, 2, 3]\n'
                          'b = [4, 5, 6]\n'
                          'c = 1',
        cases=[
            Case(
                append='b[a[c]] = -1',
                assertion=ContextAssertion(key='b', expected=[4, 5, -1])
            )
        ]
    ),
    Suite(
        preparation_lines='a = {"a": 1, "b": {} to Map[string,string],'
                          ' "c": 3}\n'
                          'b = ["a", "b", "c"]\n'
                          'c = 1\n',
        cases=[
            Case(
                append='m = a[b[c]] to Map[int,int]\n'
                       'm[1] = -1\n',
                assertion=ContextAssertion(key='a',
                                           expected={
                                               'a': 1, 'b': {}, 'c': 3
                                           })
            ),
            Case(
                append='m = a[b[c]] to Map[int,int]\n'
                       'm[1] = -1\n'
                       'a[b[c]] = m',
                assertion=ContextAssertion(key='a',
                                           expected={
                                               'a': 1, 'b': {1: -1}, 'c': 3
                                           })
            ),
        ]
    ),
    Suite(
        preparation_lines='a = ["1", 2]\n',
        cases=[
            Case(
                append='m = a to List[int]\n'
                       'm[1] = -1',
                assertion=[ContextAssertion(key='a',
                                            expected=['1', 2]),
                           ContextAssertion(key='m',
                                            expected=[1, -1])]
            ),
            Case(
                append='m = a to List[int]\n'
                       'm[1] = -1\n'
                       'a = m',
                assertion=ContextAssertion(key='a',
                                           expected=[1, -1])
            ),
            Case(
                append='m = a to List[int]\n'
                       'm[0] = 0\n'
                       'a = m',
                assertion=ContextAssertion(key='a',
                                           expected=[0, 2])
            )
        ]
    ),
    Suite(
        preparation_lines='a = {"a": "b"}',
        cases=[
            Case(append='b = "{1} {a}"',
                 assertion=ContextAssertion(key='b',
                                            expected='1 {"a": "b"}'))
        ]
    ),
    Suite(
        preparation_lines='a = 1283',
        cases=[
            Case(append='b = "{a}"',
                 assertion=ContextAssertion(key='b', expected='1283'))
        ]
    ),
    Suite(
        preparation_lines='hello = "hello"\n'
                          'world = "world"',
        cases=[
            Case(append='a = hello + world',
                 assertion=ContextAssertion(
                     key='a', expected='helloworld')),
            Case(append='a = hello + " " + world',
                 assertion=ContextAssertion(
                     key='a', expected='hello world')),
            Case(append='a = hello + " "',  # Test for no auto trim.
                 assertion=ContextAssertion(
                     key='a', expected='hello ')),
            Case(append='a = "{hello}"',
                 assertion=ContextAssertion(
                     key='a', expected='hello')),
            Case(append='a = "{hello} {world}"',
                 assertion=ContextAssertion(
                     key='a', expected='hello world')),
            Case(append='a = "{hello}{world}"',
                 assertion=ContextAssertion(
                     key='a', expected='helloworld'))
        ]
    ),
    Suite(
        preparation_lines='list = ["hello", "world"]\n'
                          'dict = {"hello": "world"}\n'
                          'file write path: "/tmp.txt" content: "hello"\n'
                          'bytes = file read path: "/tmp.txt" binary: true',
        cases=[
            Case(prepend='a = "{true}"',
                 assertion=[
                     ContextAssertion(key='a', expected='true')
                 ]),
            Case(prepend='a = "{false}"',
                 assertion=[
                     ContextAssertion(key='a', expected='false')
                 ]),
            Case(prepend='a = "{1.2}"',
                 assertion=[
                     ContextAssertion(key='a', expected='1.2')
                 ]),
            Case(prepend='a = "{1}"',
                 assertion=[
                     ContextAssertion(key='a', expected='1')
                 ]),
            Case(append='a = "{list}"',
                 assertion=[
                     ContextAssertion(
                         key='a',
                         expected='["hello", "world"]')
                 ]),
            Case(append='a = "{dict}"',
                 assertion=[
                     ContextAssertion(
                         key='a',
                         expected='{"hello": "world"}')
                 ]),
            Case(append='a = "{bytes}"',
                 assertion=[
                     ContextAssertion(
                         key='a',
                         expected='hello')
                 ])
        ]
    ),
    Suite(
        preparation_lines='a = [0]',
        cases=[
            Case(append='b = a[0]',
                 assertion=ContextAssertion(key='b', expected=0)),
            Case(append='b = a[10]',
                 assertion=RuntimeExceptionAssertion(
                     exception_type=StoryscriptRuntimeError))
        ]
    ),
    Suite(
        preparation_lines=r'm = "\n\t"',
        cases=[
            Case(append='s = m',
                 assertion=ContextAssertion(key='s', expected='\n\t')),
            Case(append=r's = "{m}\n"',
                 assertion=ContextAssertion(key='s', expected='\n\t\n')),
        ]
    ),
    Suite(
        preparation_lines='a = 1s\n'
                          'b = 10s',
        cases=[
            Case(
                append='aString = a to string',
                assertion=ContextAssertion(
                    key='aString',
                    expected='1000'
                )
            ),
            Case(
                append='sum = a + b\n'
                       'sumString = sum to string',
                assertion=ContextAssertion(
                    key='sumString',
                    expected='11000'
                )
            ),
        ]
    ),
    Suite(
        preparation_lines='a = true',
        cases=[
            Case(
                append='c = a + true',
                assertion=ContextAssertion(
                    key='c',
                    expected=2
                )
            ),
            Case(
                append='c = a + false',
                assertion=ContextAssertion(
                    key='c',
                    expected=1
                )
            )
        ]
    ),
    Suite(
        preparation_lines='a = {"a": [1, 2]}\n'
                          'b = a to Map[string,List[int]]\n'
                          'b["a"][0] = 10\n',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected={'a': [1, 2]})),
            Case(assertion=ContextAssertion(key='b', expected={'a': [10, 2]}))
        ]
    ),
    Suite(
        preparation_lines='a = {"a": {"b": "c"}}\n'
                          'b = a to Map[string,Map[string, any]]\n'
                          'b["a"]["b"] = "d"\n',
        cases=[
            Case(assertion=ContextAssertion(
                key='a', expected={'a': {'b': 'c'}})),
            Case(assertion=ContextAssertion(
                key='b', expected={'a': {'b': 'd'}}))
        ]
    )
])
@mark.asyncio
async def test_resolve_expressions(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        preparation_lines='a = "yoda"',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected='yoda'))
        ]
    ),
    Suite(
        preparation_lines='planet = "mars"',
        cases=[
            Case(assertion=ContextAssertion(key='planet',
                                            expected='mars')),
            Case(append='a = {"planet": planet, "element": "air"}',
                 assertion=ContextAssertion(key='a',
                                            expected={
                                                'planet': 'mars',
                                                'element': 'air'
                                            }))
        ]
    ),
    Suite(
        preparation_lines='planet = ["mars", "earth"]',
        cases=[
            Case(assertion=ListItemAssertion(key='planet',
                                             index=0,
                                             expected='mars')),
            Case(assertion=ListItemAssertion(key='planet',
                                             index=1,
                                             expected='earth'))
        ]
    ),
    Suite(
        preparation_lines='planet = {"name": "mars"}',
        cases=[
            Case(assertion=MapValueAssertion(key='planet',
                                             map_key='name',
                                             expected='mars'))
        ]
    ),
    Suite(
        preparation_lines='a = [0, 1, 2]',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=[0, 1, 2]))
        ]
    ),
    Suite(
        preparation_lines='a = /foo/',
        cases=[
            Case(assertion=ContextAssertion(key='a',
                                            expected=re.compile('foo')))
        ]
    ),
    Suite(
        preparation_lines='a = [true]',
        cases=[
            Case(assertion=ContextAssertion(key='a',
                                            expected=[True]))
        ]
    ),
    Suite(
        preparation_lines='i = 1\n'
                          'success = false\n'
                          'if i == 1\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 2\n'
                          'success = true\n'
                          'if i == 1\n'
                          '    success = false',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 2\n'
                          'success = false\n'
                          'if i != 1\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 1\n'
                          'success = true\n'
                          'if i != 1\n'
                          '    success = false',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = false\n'
                          'if i >= 1\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = false\n'
                          'if i >= 5\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = true\n'
                          'if i >= 6\n'
                          '    success = false',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = true\n'
                          'if i > 5\n'
                          '    success = false',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = false\n'
                          'if i > 4\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = true\n'
                          'if i < 5\n'
                          '    success = false',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = false\n'
                          'if i < 6\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = false\n'
                          'if i <= 5\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = true\n'
                          'if i <= 4\n'
                          '    success = false',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = 5\n'
                          'success = false\n'
                          'if i <= 6\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = false\n'
                          'success = true\n'
                          'if i\n'
                          '    success = false',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = true\n'
                          'success = false\n'
                          'if i\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = true\n'
                          'success = true\n'
                          'if not i\n'
                          '    success = false',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = false\n'
                          'success = false\n'
                          'if not i\n'
                          '    success = true',
        cases=[
            Case(assertion=ContextAssertion(key='success', expected=True))
        ]
    ),
    Suite(
        preparation_lines='i = null\n'
                          'status = 0\n',
        cases=[
            Case(append='if i == null\n'
                        '    status = 1',
                 assertion=ContextAssertion(key='status',
                                            expected=1)),
            Case(append='if not(i == null)\n'
                        '    status = 2',
                 assertion=ContextAssertion(key='status',
                                            expected=0)),
        ]
    ),
])
@mark.asyncio
async def test_resolve_all_objects(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        cases=[
            Case(append='a = [0] to List[int]',
                 assertion=ContextAssertion(key='a', expected=[0])),
            Case(append='a = [] to List[int]',
                 assertion=ContextAssertion(key='a', expected=[])),
            Case(append='a = ["3", "2"] to List[int]',
                 assertion=ContextAssertion(key='a', expected=[3, 2])),
            Case(append='a = 2 to float',
                 assertion=ContextAssertion(key='a', expected=2.)),
            Case(append='a = 2.5 to int',
                 assertion=ContextAssertion(key='a', expected=2)),
            Case(append='a = 2 to string',
                 assertion=ContextAssertion(key='a', expected='2')),
            Case(append='a = {2: "42"} to Map[float,float]',
                 assertion=ContextAssertion(key='a', expected={2.: 42.})),
            Case(append='a = "foo" to regex',
                 assertion=ContextAssertion(key='a',
                                            expected=re.compile('foo'))),
            Case(append='a = /foo/ to regex',
                 assertion=ContextAssertion(key='a',
                                            expected=re.compile('foo'))),
            Case(append='a = 2 to any',
                 assertion=ContextAssertion(key='a', expected=2)),
            Case(append='a = true to int',
                 assertion=ContextAssertion(key='a', expected=1)),
            Case(append='a = false to int',
                 assertion=ContextAssertion(key='a', expected=0)),
            Case(append='a = {"foo": 42} to Map[string,int]',
                 assertion=ContextAssertion(key='a',
                                            expected={'foo': 42})),
            Case(append='a = {} to Map[int,boolean]',
                 assertion=ContextAssertion(key='a',
                                            expected={}))
        ]
    ),
    Suite(
        preparation_lines='arr = [] to List[any]\n'
                          'arr = arr.append(item: 42)\n'
                          'b = arr[0]',
        cases=[
            Case(append='c = b to List[int]',
                 assertion=RuntimeExceptionAssertion(
                     TypeAssertionRuntimeError,
                     message='Incompatible type assertion: Received 42 '
                             '(int), but expected List[int]')),
            Case(append='c = b to Map[int,string]',
                 assertion=RuntimeExceptionAssertion(
                     TypeAssertionRuntimeError,
                     message='Incompatible type assertion: Received 42 '
                             '(int), but expected Map[int,string]')),
            Case(append='b=/foo/\nc = b to List[int]',
                 assertion=RuntimeExceptionAssertion(
                     TypeAssertionRuntimeError,
                     message='Incompatible type assertion: Received /foo/ '
                             '(regexp), but expected List[int]')),
        ]
    ),
    Suite(
        cases=[
            Case(append='c = "foo" to float',
                 assertion=RuntimeExceptionAssertion(
                     TypeValueRuntimeError,
                     message='Type conversion failed from str to float '
                             'with `foo`')),
            Case(append='c = "foo" to int',
                 assertion=RuntimeExceptionAssertion(
                     TypeValueRuntimeError,
                     message='Type conversion failed from str to int '
                             'with `foo`')),
            Case(append='c = "foo" to string',
                 assertion=ContextAssertion(key='c', expected='foo')),
            Case(append='c = "10" to int',
                 assertion=ContextAssertion(key='c', expected=10)),
            Case(append='c = "10.1" to float',
                 assertion=ContextAssertion(key='c', expected=10.1)),
            Case(append='c = [0, 1, 2] to string',
                 assertion=ContextAssertion(key='c', expected='[0, 1, 2]')),
            Case(append='c = {"a": "b", "c": 10} to string',
                 assertion=ContextAssertion(
                     key='c', expected='{"a": "b", "c": 10}')),
            Case(append='c = [{"a":"b"}, {}, {"c": 10}] to string',
                 assertion=ContextAssertion(
                     key='c', expected='[{"a": "b"}, {}, {"c": 10}]')),
        ]
    )
])
@mark.asyncio
async def test_type_casts(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        preparation_lines='i = 0\n'
                          'total = 0\n'
                          'while i <= 10\n'
                          '    current = i\n'
                          '    i = current + 1\n'
                          '    total += current',
        cases=[
            Case(assertion=ContextAssertion(key='current', expected=None)),
            Case(assertion=ContextAssertion(key='total', expected=55)),
            Case(assertion=ContextAssertion(key='i', expected=11))
        ]
    ),
    Suite(
        preparation_lines='name = "nobody"\n'

                          'function sayHello name: string\n'
                          '    prefix = "Hello"\n'
                          '    greeting = "{prefix} {name}"\n'
                          '    log info msg: greeting\n'

                          'l = [1, 2, 3]\n'
                          'total = 0\n'

                          'foreach l as x\n'
                          '    sayHello(name: "user")\n'
                          '    total += x',
        cases=[
            Case(assertion=ContextAssertion(key='total',
                                            expected=6)),
            Case(assertion=ContextAssertion(key='prefix',
                                            expected=None)),
            Case(assertion=ContextAssertion(key='name',
                                            expected='nobody'))
        ]
    ),
    Suite(
        preparation_lines='if true\n'
                          '  a = 0\n'
                          'if true\n'
                          '  a = 1\n',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=1))
        ]
    ),
])
@mark.asyncio
async def test_stacked_contexts(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        preparation_lines='labels = [{"name": "a"}]\n'
                          'found = false',
        cases=[
            Case(
                append='foreach labels as label\n'
                       '   if label["name"] == "a" or label["name"] == "b"\n'
                       '        found = true\n'
                       'outside = true',
                assertion=[ContextAssertion(key='found', expected=True),
                           ContextAssertion(key='outside', expected=True)]
            )
        ]
    ),
    Suite(
        preparation_lines='l = [8, 9, 10]\n'
                          'index_sum = 0\n'
                          'value_sum = 0\n'
                          'foreach l as index, value\n'
                          '  index_sum += index\n'
                          '  value_sum += value\n',
        cases=[
            Case(
                assertion=ContextAssertion(key='index_sum', expected=3)
            ),
            Case(
                assertion=ContextAssertion(key='value_sum', expected=27)
            )
        ]
    ),
    Suite(
        preparation_lines='d = {"a": 8, "b": 9, "c": 10}\n'
                          'key_string = ""\n'
                          'value_sum = 0\n'
                          'foreach d as key\n'
                          '  key_string += key\n'
                          '  value_sum += d[key]\n',
        cases=[
            Case(
                assertion=ContextAssertion(key='key_string', expected='abc')
            ),
            Case(
                assertion=ContextAssertion(key='value_sum', expected=27)
            )
        ]
    ),
    Suite(
        preparation_lines='d = {"a": 8, "b": 9, "c": 10}\n'
                          'key_string = ""\n'
                          'value_sum = 0\n'
                          'foreach d as key, value\n'
                          '  key_string += key\n'
                          '  value_sum += value\n',
        cases=[
            Case(
                assertion=ContextAssertion(key='key_string', expected='abc')
            ),
            Case(
                assertion=ContextAssertion(key='value_sum', expected=27)
            )
        ]
    ),
    Suite(
        preparation_lines='a = [1, 2, 3, 4, 5]\n'
                          'b = [] to List[int]\n'
                          'c = [] to List[int]\n',
        cases=[
            Case(append='foreach a as elem\n'
                        '   b = b.append(item: elem)\n'
                        '   foreach b as elem2\n'
                        '       if elem2 > 1\n'
                        '           break\n'
                        '       c = c.append(item: elem2)\n',
                 assertion=[
                     ContextAssertion(key='b', expected=[1, 2, 3, 4, 5]),
                     ContextAssertion(key='c', expected=[1, 1, 1, 1, 1])
                 ])
        ]
    ),
    Suite(
        preparation_lines='a = [1, 1, 1, 2, 3, 4, 5]\n'
                          'b = 0\n',
        cases=[
            Case(append='b = a[b]',
                 assertion=ContextAssertion(key='b', expected=1)),
            Case(append='foreach a as elem\n'
                        '   b = b + elem\n'
                        '   if b == 3\n'
                        '       break',
                 assertion=ContextAssertion(key='b', expected=3))
        ]
    ),
    Suite(
        preparation_lines='a = [1, 1, 1, 2, 3, 4, 5]\n'
                          'b = 0\n',
        cases=[
            Case(append='foreach a as elem\n'
                        '   if elem % 2 == 0\n'
                        '       continue\n'
                        '   b = b + elem\n',
                 assertion=ContextAssertion(key='b', expected=11))
        ]
    ),
])
@mark.asyncio
async def test_foreach(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    # while loop
    Suite(
        preparation_lines='i = 0',
        cases=[
            Case(
                append='while i < 10\n'
                       '   i = i + 1\n'
                       'outside = true',
                assertion=[ContextAssertion(key='outside', expected=True),
                           ContextAssertion(key='i', expected=10)])
        ]
    ),
    # while loop
    Suite(
        preparation_lines='i = 0\na = 0',
        cases=[
            Case(
                append='while i < 100\n'
                       '    a = 0\n'
                       '    while a < 10\n'
                       '      i = i + 1\n'
                       '      a = a + 1\n'
                       'outside = true',
                assertion=[ContextAssertion(key='outside', expected=True),
                           ContextAssertion(key='i', expected=100),
                           ContextAssertion(key='a', expected=10)])
        ]
    ),
    Suite(
        preparation_lines='i = 0',
        cases=[
            Case(
                append='while i < 5000 or true\n'
                       '   i = i + 1\n',
                assertion=RuntimeExceptionAssertion(
                    exception_type=StoryscriptRuntimeError,
                    context_assertion=ContextAssertion(
                        key='i',
                        expected=100000
                    )
                )
            )
        ]
    ),
    # while loop
    Suite(
        preparation_lines='function foo returns boolean\n'
                          '   while true\n'
                          '      return true\n',
        cases=[
            Case(
                append='value = foo()',
                assertion=ContextAssertion(
                    key='value',
                    expected=True
                )
            )
        ]
    ),
])
@mark.asyncio
async def test_while(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        preparation_lines='a = 1\n'
                          'if true and false\n'
                          '    a = 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=1))
        ]
    ),
    Suite(
        preparation_lines='a = 1\n'
                          'if false and true\n'
                          '    a = 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=1))
        ]
    ),
    Suite(
        preparation_lines='a = 1\n'
                          'b = 5\n'
                          'c = null\n',
        cases=[
            Case(append='if true or false\n'
                        '   c = "true"',
                 assertion=ContextAssertion(key='c', expected='true')),
            Case(append='if false or true\n'
                        '   c = "true"',
                 assertion=ContextAssertion(key='c', expected='true')),
            Case(append='if true\n'
                        '   c = "true"',
                 assertion=ContextAssertion(key='c', expected='true')),
            Case(append='if false\n'
                        '   c = "wtf"',
                 assertion=ContextAssertion(key='c', expected=None)),
            Case(append='if a == 100 or b == 100\n'
                        '   c = "wtf"',
                 assertion=ContextAssertion(key='c', expected=None)),
            Case(append='if a == 100 or b == 5\n'
                        '   c = "b"',
                 assertion=ContextAssertion(key='c', expected='b')),
            Case(append='if a == 1 or b == 100\n'
                        '   c = "a"',
                 assertion=ContextAssertion(key='c', expected='a')),
            Case(append='if a == 1 or b == 5\n'
                        '   c = "a"',
                 assertion=ContextAssertion(key='c', expected='a')),
            Case(append='if a == 100 or b == 100 or true\n'
                        '   c = "true"',
                 assertion=ContextAssertion(key='c', expected='true'))
        ]
    ),
    Suite(
        preparation_lines='if colour == "blue"\n'
                          '  result = "blue"\n'
                          'else if colour == "red"\n'
                          '  result = "red"\n'
                          'else if colour == "yellow"\n'
                          '  result = "yellow"\n'
                          'else if colour == "green"\n'
                          '  result = "green"\n'
                          'else\n'
                          '  result = "unknown"\n'
                          'outside_var = "executed"\n',
        cases=[
            Case(prepend='colour = "blue"',
                 assertion=[ContextAssertion(key='result',
                                             expected='blue'),
                            ContextAssertion(key='outside_var',
                                             expected='executed')]),

            Case(prepend='colour = "red"',
                 assertion=[ContextAssertion(key='result',
                                             expected='red'),
                            ContextAssertion(key='outside_var',
                                             expected='executed')]),

            Case(prepend='colour = "yellow"',
                 assertion=[ContextAssertion(key='result',
                                             expected='yellow'),
                            ContextAssertion(key='outside_var',
                                             expected='executed')]),

            Case(prepend='colour = "green"',
                 assertion=[ContextAssertion(key='result',
                                             expected='green'),
                            ContextAssertion(key='outside_var',
                                             expected='executed')]),

            Case(prepend='colour = "pink"',
                 assertion=[ContextAssertion(key='result',
                                             expected='unknown'),
                            ContextAssertion(key='outside_var',
                                             expected='executed')])
        ]
    ),
])
@mark.asyncio
async def test_if_else(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        preparation_lines='function a\n'
                          '    a()\n'
                          'a()',
        cases=[
            Case(assertion=RuntimeExceptionAssertion(
                exception_type=StackOverflowException))
        ]
    ),
    Suite(
        preparation_lines='function is_even n:int returns boolean\n'
                          '    if n % 2 == 0\n'
                          '        return true\n'
                          '    else\n'
                          '        return false\n'
                          '\n'
                          'even = is_even(n: a)',  # a is prepended.
        cases=[
            Case(prepend='a = 10',
                 assertion=ContextAssertion(key='even', expected=True)),
            Case(prepend='a = 11',
                 assertion=ContextAssertion(key='even', expected=False))
        ]
    ),
    Suite(
        preparation_lines='function echo i:int returns int\n'
                          '    return i\n'
                          '\n'
                          'x = 500\n'
                          'function add a:int b:int returns int\n'
                          '    return a + b\n'
                          '\n'
                          'function get_28 returns int\n'
                          '    return 28\n'
                          '\n'
                          'y=30*x\n'
                          'function do_nothing\n'
                          '    a = "nothing meaningful happened"\n',
        cases=[
            Case(append='a = echo(i: 200)',
                 assertion=ContextAssertion(key='a', expected=200)),
            Case(append='a = echo(i: -1)',
                 assertion=ContextAssertion(key='a', expected=-1)),
            Case(append='a = echo(i: 28)',
                 assertion=ContextAssertion(key='a', expected=28)),
            Case(append='echo(i: 28)',
                 assertion=[]),
            Case(append='a = add(a: 10 b: 20)',
                 assertion=ContextAssertion(key='a', expected=30)),
            Case(append='a = add(a: 10 b: 20) + get_28()',
                 assertion=ContextAssertion(key='a', expected=58)),
            Case(append='a = get_28()',
                 assertion=ContextAssertion(key='a', expected=28)),
            Case(append='do_nothing()',
                 assertion=ContextAssertion(key='a', expected=None)),
        ]
    ),
    Suite(
        cases=[
            Case(append='a = echo(i: 200)\n'
                        'function echo i:int returns int\n'
                        '    return i\n',
                 assertion=ContextAssertion(key='a', expected=200)),
        ]
    ),
])
@mark.asyncio
async def test_function(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        preparation_lines='try\n'
                          '  throw "error"\n'
                          'catch\n'
                          '  failed = true\n',
        cases=[
            Case(prepend='failed = false',
                 assertion=ContextAssertion(key='failed', expected=True))
        ]
    ),
    Suite(
        preparation_lines='try\n'
                          '  throw "error"\n'
                          'catch\n'
                          '  failed = true\n'
                          'finally\n'
                          '  _finally = true',
        cases=[
            Case(prepend='failed = false',
                 assertion=ContextAssertion(key='failed', expected=True)),

            Case(prepend='_finally = false',
                 assertion=ContextAssertion(key='_finally', expected=True))
        ]
    ),
    Suite(
        preparation_lines='try\n'
                          '  throw "error"\n'
                          'catch\n'
                          '  failed = true\n'
                          'finally\n'
                          '  failed = false',
        cases=[
            Case(prepend='failed = false',
                 assertion=ContextAssertion(key='failed', expected=False))
        ]
    ),
    Suite(
        preparation_lines='try\n'
                          '  throw "error"\n'
                          'catch\n'
                          '  throw "catch error"\n'
                          'finally\n'
                          '  _finally = true',
        cases=[
            Case(prepend='_finally = false',
                 assertion=RuntimeExceptionAssertion(
                     exception_type=StoryscriptError,
                     context_assertion=ContextAssertion(
                         key='_finally', expected=True
                     )
                 )),
        ]
    ),
    Suite(
        preparation_lines='try\n'
                          '  throw "error"\n'
                          'catch\n'
                          '  error = "two"\n'
                          '  try\n'
                          '    throw "error"\n'
                          '  catch\n'
                          '    error = "three"',
        cases=[
            Case(prepend='error = "one"',
                 assertion=ContextAssertion(key='error', expected='three'))
        ]
    ),
    Suite(
        preparation_lines='try\n'
                          '  try\n'
                          '    throw "error"\n'
                          '  catch\n'
                          '    result = true\n'
                          'catch\n'
                          '  result = false\n',
        cases=[
            Case(prepend='result = false',
                 assertion=ContextAssertion(key='result', expected=True))
        ]
    ),
    Suite(
        preparation_lines='try\n'
                          '  try\n'
                          '    throw "error"\n'
                          '  catch\n'
                          '    try\n'
                          '      throw "error"\n'
                          '    catch\n'
                          '      result = true\n'
                          'catch\n'
                          '  result = false\n',
        cases=[
            Case(prepend='result = false',
                 assertion=ContextAssertion(key='result', expected=True))
        ]
    ),
    Suite(
        preparation_lines='try\n'
                          '  try\n'
                          '    throw "error1"\n'
                          '  catch\n'
                          '    try\n'
                          '      throw "error2"\n'
                          '    catch\n'
                          '      throw "error3"\n'
                          'catch\n'
                          '  try\n'
                          '    throw "error4"\n'
                          '  catch\n'
                          '    try\n'
                          '       throw "error5"\n'
                          '    catch\n'
                          '       result = true\n',
        cases=[
            Case(prepend='result = false',
                 assertion=ContextAssertion(key='result', expected=True))
        ]
    ),
    Suite(
        preparation_lines='try\n'
                          '  try\n'
                          '    throw "error"\n'
                          '  catch\n'
                          '    err1 = "1"\n'
                          '    try\n'
                          '      throw "error"\n'
                          '    catch\n'
                          '      err2 = "2"\n'
                          '      throw "error"\n'
                          '    finally\n'
                          '      result1 = "1"\n'
                          '  finally\n'
                          '    result2 = "2"\n'
                          'catch\n'
                          '  err3 = "3"\n'
                          '  try\n'
                          '    throw "error"\n'
                          '  catch\n'
                          '    err4 = "4"\n'
                          '    try\n'
                          '       throw "error"\n'
                          '    catch\n'
                          '       err5 = "5"\n'
                          '    finally\n'
                          '       result3 = "3"\n'
                          '  finally\n'
                          '    result4 = "4"\n'
                          'finally\n'
                          '  result0 = "0"',
        cases=[
            Case(prepend='result0 = ""\n'
                         'result1 = ""\n'
                         'result2 = ""\n'
                         'result3 = ""\n'
                         'result4 = ""\n'
                         'err0 = ""\n'
                         'err1 = ""\n'
                         'err2 = ""\n'
                         'err3 = ""\n'
                         'err4 = ""\n'
                         'err5 = ""',
                 assertion=[
                     ContextAssertion(
                         key='result0', expected='0'
                     ),
                     ContextAssertion(
                         key='result1', expected='1'
                     ),
                     ContextAssertion(
                         key='result2', expected='2'
                     ),
                     ContextAssertion(
                         key='result3', expected='3'
                     ),
                     ContextAssertion(
                         key='result4', expected='4'
                     ),
                     ContextAssertion(
                         key='err1', expected='1'
                     ),
                     ContextAssertion(
                         key='err2', expected='2'
                     ),
                     ContextAssertion(
                         key='err3', expected='3'
                     ),
                     ContextAssertion(
                         key='err4', expected='4'
                     ),
                     ContextAssertion(
                         key='err5', expected='5'
                     )
                 ])
        ]
    ),
    Suite(preparation_lines='function test a: int b: int returns string\n'
                            '    try\n'
                            '        if a % 2 == 0\n'
                            '            return "even"\n'
                            '        a = a / b\n'
                            '    catch\n'
                            '        return "error"\n'
                            '    finally\n'
                            '        if a % 2 == 0 and b == 0\n'
                            '            return "evenoverride"\n'
                            '    return "odd"\n',
          cases=[
              Case(append='a = test(a: 10 b: 1)',
                   assertion=ContextAssertion(key='a', expected='even')),
              Case(append='a = test(a: 10 b: 0)',
                   assertion=RuntimeExceptionAssertion(
                       exception_type=StoryscriptError,
                       message='Invalid usage of keyword "return".'
                   )),
              Case(append='a = test(a: 11 b: 0)',
                   assertion=ContextAssertion(key='a', expected='error'))
          ])
])
@mark.asyncio
async def test_try_catch(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)
