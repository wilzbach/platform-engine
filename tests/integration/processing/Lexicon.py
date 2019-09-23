# -*- coding: utf-8 -*-
import math
import re
import sys
import tempfile
from unittest.mock import MagicMock

from pytest import mark

from storyruntime.Exceptions import StackOverflowException, StoryscriptError, \
    StoryscriptRuntimeError, TypeAssertionRuntimeError, TypeValueRuntimeError
from storyruntime.Story import Story
from storyruntime.processing import Stories
from storyruntime.processing.internal import File, Http, Json, Log

import storyscript

from .Assertions import ContextAssertion, IsANumberAssertion, \
    ListItemAssertion, MapValueAssertion, RuntimeExceptionAssertion


class Case:
    def __init__(self, append=None, prepend=None, assertion=None):
        self.append = append
        self.prepend = prepend
        self.assertion = assertion


class Suite:
    def __init__(self, cases, preparation_lines=''):
        self.cases = cases
        self.preparation_lines = preparation_lines


@mark.parametrize('suite', [  # See pydoc below for how this runs.
    Suite(
        preparation_lines='a = {"key_1": "val_1"}',
        cases=[
            Case(append='b = a["foo"]',
                 assertion=RuntimeExceptionAssertion(
                     exception_type=StoryscriptRuntimeError)),
            Case(append='b = a.get(key: "foo" default: "def_val")',
                 assertion=ContextAssertion(key='b', expected='def_val')),
            Case(append='b = a.get(key: "foo" default: null)',
                 assertion=ContextAssertion(key='b', expected=None)),
            Case(append='b = a.get(key: "key_1" default: null)',
                 assertion=ContextAssertion(key='b', expected='val_1')),
            Case(append='b = a["key_1"]',
                 assertion=ContextAssertion(key='b', expected='val_1'))
        ]
    ),
    Suite(
        preparation_lines='a = {"a": "b"}',
        cases=[
            Case(append='b = "{1} {a}"',
                 assertion=ContextAssertion(key='b',
                                            expected='1 {\'a\': \'b\'}'))
        ]
    ),
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
        preparation_lines='a = json stringify content: {"a": "b"}',
        cases=[
            Case(assertion=ContextAssertion(key='a',
                                            expected='{"a": "b"}'))
        ]
    ),
    Suite(
        preparation_lines='a = http fetch '
                          'url: "https://stories.storyscriptapp.com/status"',
        cases=[
            Case(assertion=ContextAssertion(
                key='a',
                expected='OK'
            ))
        ]
    ),
    Suite(
        preparation_lines='a = http fetch '
                          'url: "https://www.google.com/"\n'
                          'passed = true',
        cases=[
            Case(assertion=ContextAssertion(
                key='passed',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='a = http fetch '
                          'url: "https://jsonplaceholder.'
                          'typicode.com/todos/1"\n'
                          'passed = true',
        cases=[
            Case(assertion=ContextAssertion(
                key='passed',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='exists = file exists path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='exists',
                expected=False
            ))
        ]
    ),
    Suite(
        preparation_lines='file mkdir path: "file"\n'
                          'exists = file exists path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='exists',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='file mkdir path: "/file"\n'
                          'exists = file exists path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='exists',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='file mkdir path: "file"\n'
                          'exists = file exists path: "/file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='exists',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" '
                          'content: "hello world"\n'
                          'exists = file exists path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='exists',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='file mkdir path: "file"\n'
                          'exists = file exists path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='exists',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='file mkdir path: "file"\n'
                          'isDir = file isDir path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='isDir',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" content: "file"\n'
                          'file mkdir path: "path"\n'
                          'files = file list\n',
        cases=[
            Case(assertion=ContextAssertion(
                key='files',
                expected=['/file', '/path']
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" content: "file"\n'
                          'file mkdir path: "path/anotherdir"\n'
                          'files = file list\n',
        cases=[
            Case(assertion=ContextAssertion(
                key='files',
                expected=['/file', '/path']
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" content: "file"\n'
                          'file mkdir path: "path/anotherdir"\n'
                          'files = file list recursive: true\n',
        cases=[
            Case(assertion=ContextAssertion(
                key='files',
                expected=['/file', '/path', '/path/anotherdir']
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" content: "file"\n'
                          'file mkdir path: "path/anotherdir"\n'
                          'file write path: "/path/anotherdir/file" '
                          'content: "file"\n'
                          'files = file list recursive: true\n',
        cases=[
            Case(assertion=ContextAssertion(
                key='files',
                expected=[
                    '/file',
                    '/path',
                    '/path/anotherdir',
                    '/path/anotherdir/file'
                ]
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" content: "file"\n'
                          'isDir = file isDir path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='isDir',
                expected=False
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" content: "file"\n'
                          'isFile = file isFile path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='isFile',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='file mkdir path: "file"\n'
                          'isFile = file isFile path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='isFile',
                expected=False
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" content: "file"\n'
                          'data = file read path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='data',
                expected='file'
            ))
        ]
    ),
    Suite(
        preparation_lines='file mkdir path: "/file/data"\n'
                          'data = file isDir path: "file"',
        cases=[
            Case(assertion=ContextAssertion(
                key='data',
                expected=True
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" binary: true '
                          'content: "hello world"\n'
                          'data = file read path: "file" binary: true',
        cases=[
            Case(assertion=ContextAssertion(
                key='data',
                expected=b'hello world'
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" binary: true '
                          'content: "hello world"\n'
                          'data = file read path: "file" binary: false',
        cases=[
            Case(assertion=ContextAssertion(
                key='data',
                expected='hello world'
            ))
        ]
    ),
    Suite(
        preparation_lines='file write path: "file" binary: false '
                          'content: "hello world"\n'
                          'data = file read path: "file" binary: true',
        cases=[
            Case(assertion=ContextAssertion(
                key='data',
                expected=b'hello world'
            ))
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
                          'if true and false\n'
                          '    a = 2',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=1))
        ]
    ),
    Suite(
        preparation_lines='a = 1283',
        cases=[
            Case(append='b = a + ""',
                 assertion=ContextAssertion(key='b', expected='1283'))
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
    Suite(
        preparation_lines='my_list = [1, 2, 3]',
        cases=[
            Case(append='a = (my_list.length()) + 4',
                 assertion=ContextAssertion(key='a', expected=7)),
            Case(append='a = my_list[0]',
                 assertion=ContextAssertion(key='a', expected=1)),
            Case(append='a = my_list[-1]',
                 assertion=ContextAssertion(key='a', expected=3)),
        ]
    ),
    Suite(
        preparation_lines='status = "opened"\n'
                          'tag = "priority"\n'
                          'if status == "opened" and '
                          '["important", "priority"].contains(item: tag)\n'
                          '   a = 1',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=1))
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
                         expected='[\'hello\', \'world\']')
                 ]),
            Case(append='a = "{dict}"',
                 assertion=[
                     ContextAssertion(
                         key='a',
                         expected='{\'hello\': \'world\'}')
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
        preparation_lines='a = [1, 2, 3, 4, 5]\n'
                          'b = [] as List[int]\n'
                          'c = [] as List[int]\n',
        cases=[
            Case(append='foreach a as elem\n'
                        '   b.append(item: elem)\n'
                        '   foreach b as elem2\n'
                        '       if elem2 > 1\n'
                        '           break\n'
                        '       c.append(item: elem2)\n',
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
    Suite(
        preparation_lines='str = "hello world!"',
        cases=[
            Case(append='len = str.length()',
                 assertion=ContextAssertion(key='len', expected=12)),

            Case(append='r = str.contains(item: "hello")',
                 assertion=ContextAssertion(key='r', expected=True)),

            Case(append='r = str.contains(item: "hello1")',
                 assertion=ContextAssertion(key='r', expected=False)),

            Case(append='r = str.contains(pattern: /llo/)',
                 assertion=ContextAssertion(key='r', expected=True)),

            Case(append='r = str.contains(pattern: /f/)',
                 assertion=ContextAssertion(key='r', expected=False)),

            Case(append='parts = str.split(by: " ")',
                 assertion=ContextAssertion(
                     key='parts', expected=['hello', 'world!'])),

            Case(append='parts = str.split(by: "")',
                 assertion=ContextAssertion(
                     key='parts', expected=[
                         'h', 'e', 'l', 'l', 'o', ' ',
                         'w', 'o', 'r', 'l', 'd', '!'
                     ])),

            Case(append='a = str.uppercase()',
                 assertion=ContextAssertion(
                     key='a', expected='HELLO WORLD!')),

            Case(append='a = str.lowercase()',
                 assertion=ContextAssertion(
                     key='a', expected='hello world!')),

            Case(append='a = str.capitalize()',
                 assertion=ContextAssertion(
                     key='a', expected='Hello World!')),

            Case(append='a = str.substring(start: 2)',
                 assertion=ContextAssertion(
                     key='a', expected='llo world!')),

            Case(append='a = str.substring(start: 2).substring(end: -3)',
                 assertion=ContextAssertion(
                     key='a', expected='llo wor')),

            Case(append='a = str.substring(end: 5)',
                 assertion=ContextAssertion(
                     key='a', expected='hello')),

            Case(append='a = str.substring(start: 6 end: 11)',
                 assertion=ContextAssertion(
                     key='a', expected='world')),

            Case(append='a = str.substring(start: 6 end: -2)',
                 assertion=ContextAssertion(
                     key='a', expected='worl')),

            Case(append='a = str.substring(start: 6 end: -6)',
                 assertion=ContextAssertion(
                     key='a', expected='')),

            Case(append='a = str.substring(start: 20)',
                 assertion=ContextAssertion(
                     key='a', expected='')),

            Case(append='a = str.substring(start: 10 end:20)',
                 assertion=ContextAssertion(
                     key='a', expected='d!')),

            Case(append='a = str.substring(start: -3)',
                 assertion=ContextAssertion(
                     key='a', expected='ld!')),

            Case(append='a = str.startswith(prefix: "hello")',
                 assertion=ContextAssertion(
                     key='a', expected=True)),

            Case(append='a = str.startswith(prefix: "ello")',
                 assertion=ContextAssertion(
                     key='a', expected=False)),

            Case(append='a = str.endswith(suffix: "!")',
                 assertion=ContextAssertion(
                     key='a', expected=True)),

            Case(append='a = str.endswith(suffix: ".")',
                 assertion=ContextAssertion(
                     key='a', expected=False)),
        ]
    ),
    Suite(
        preparation_lines='str = "hello."',
        cases=[
            Case(append='r = str.replace(item: "hello" by:"foo")',
                 assertion=ContextAssertion(key='r', expected='foo.')),

            Case(append='r = str.replace(item: "l" by:"o")',
                 assertion=ContextAssertion(key='r', expected='heooo.')),

            Case(append='r = str.replace(item: "k" by:"$")',
                 assertion=ContextAssertion(key='r', expected='hello.')),

            Case(append='r = str.replace(pattern: /hello/ by:"foo")',
                 assertion=ContextAssertion(key='r', expected='foo.')),

            Case(append='r = str.replace(pattern: /l/ by:"o")',
                 assertion=ContextAssertion(key='r', expected='heooo.')),

            Case(append='r = str.replace(pattern: /k/ by:"$")',
                 assertion=ContextAssertion(key='r', expected='hello.')),
        ]
    ),
    Suite(
        preparation_lines='str = " text "',
        cases=[
            Case(append='a = str.trim()',
                 assertion=ContextAssertion(
                     key='a', expected='text')),
        ],
    ),
    Suite(
        preparation_lines='e = 10\n'
                          'o = -3',
        cases=[
            Case(append='a = e.isOdd()',
                 assertion=ContextAssertion(key='a', expected=False)),

            Case(append='a = o.isOdd()',
                 assertion=ContextAssertion(key='a', expected=True)),

            Case(append='a = e.isEven()',
                 assertion=ContextAssertion(key='a', expected=True)),

            Case(append='a = o.isEven()',
                 assertion=ContextAssertion(key='a', expected=False)),

            Case(append='a = o.absolute()',
                 assertion=[
                     ContextAssertion(key='a', expected=3),
                     ContextAssertion(key='o', expected=-3)
                 ]),

            Case(append='a = e.increment()',
                 assertion=[
                     ContextAssertion(key='a', expected=11),
                     ContextAssertion(key='e', expected=10)
                 ]),

            Case(append='a = e.decrement()',
                 assertion=[
                     ContextAssertion(key='a', expected=9),
                     ContextAssertion(key='e', expected=10)
                 ]),

            Case(append='e.decrement()',
                 assertion=ContextAssertion(key='e', expected=10)),

            Case(append='e.increment()',
                 assertion=ContextAssertion(key='e', expected=10)),

            Case(append='a = e.increment().increment()',
                 assertion=ContextAssertion(key='a', expected=12)),

            Case(append='a = 5.increment().increment()',
                 assertion=ContextAssertion(key='a', expected=7)),

            Case(append='a = -5.increment().increment()',
                 assertion=ContextAssertion(key='a', expected=-3)),

            Case(append='a = (-5).increment().increment()',
                 assertion=ContextAssertion(key='a', expected=-3)),
        ]
    ),
    Suite(
        preparation_lines='m = {"a": 1, "b": 2}',
        cases=[
            Case(append='s = m.length()',
                 assertion=ContextAssertion(key='s', expected=2)),

            Case(append='s = m.keys()',
                 assertion=ContextAssertion(key='s', expected=['a', 'b'])),

            Case(append='s = m.values()',
                 assertion=ContextAssertion(key='s', expected=[1, 2])),

            Case(append='s = m.flatten()',
                 assertion=ContextAssertion(
                     key='s', expected=[['a', 1], ['b', 2]])),

            Case(append='s = m.remove(key: "a")',
                 assertion=[
                     ContextAssertion(key='s', expected={'b': 2}),
                     ContextAssertion(key='m', expected={'a': 1, 'b': 2}),
                 ]),

            Case(append='s = m.remove(key: "c")',
                 assertion=[
                     ContextAssertion(key='s', expected={'a': 1, 'b': 2}),
                     ContextAssertion(key='m', expected={'a': 1, 'b': 2}),
                 ]),

            Case(append='s = m.get(key: "a" default: 3)',
                 assertion=[
                     ContextAssertion(key='s', expected=1),
                     ContextAssertion(key='m', expected={'a': 1, 'b': 2})
                 ]),

            Case(append='s = m.get(key: "c" default: 42)',
                 assertion=ContextAssertion(key='s', expected=42)),

            Case(append='s = m.contains(key: "d")',
                 assertion=ContextAssertion(key='s', expected=False)),

            Case(append='s = m.contains(key: "a")',
                 assertion=ContextAssertion(key='s', expected=True)),

            Case(append='s = m.contains(value: 3)',
                 assertion=ContextAssertion(key='s', expected=False)),

            Case(append='s = m.contains(value: 1)',
                 assertion=ContextAssertion(key='s', expected=True)),

            Case(append='key = "a"\ns = m[key]',
                 assertion=ContextAssertion(key='s', expected=1)),
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
        preparation_lines='arr = [1, 2, 2, 3, 4, 4, 5, 5]',
        cases=[
            Case(append='actual = arr.index(of: 5)',
                 assertion=ContextAssertion(key='actual', expected=6)),

            Case(append='actual = arr.index(of: 500)',
                 assertion=ContextAssertion(key='actual', expected=-1)),

            Case(append='actual = arr.length()',
                 assertion=ContextAssertion(key='actual', expected=8)),

            Case(append='arr.append(item: 6)',
                 assertion=ContextAssertion(
                     key='arr', expected=[1, 2, 2, 3, 4, 4, 5, 5, 6])),

            Case(append='arr.prepend(item: 1)',
                 assertion=ContextAssertion(
                     key='arr', expected=[1, 1, 2, 2, 3, 4, 4, 5, 5])),

            Case(append='r = arr.random()',
                 assertion=IsANumberAssertion(key='r')),

            Case(append='arr.reverse()',
                 assertion=ContextAssertion(
                     key='arr', expected=[5, 5, 4, 4, 3, 2, 2, 1])),

            Case(append='arr.sort()',
                 assertion=ContextAssertion(
                     key='arr', expected=[1, 2, 2, 3, 4, 4, 5, 5])),

            Case(append='min = arr.min()',
                 assertion=ContextAssertion(key='min', expected=1)),

            Case(append='max = arr.max()',
                 assertion=ContextAssertion(key='max', expected=5)),

            Case(append='sum = arr.sum()',
                 assertion=ContextAssertion(key='sum', expected=26)),

            Case(append='arr.unique()',
                 assertion=ContextAssertion(
                     key='arr', expected=[1, 2, 3, 4, 5])),

            Case(append='a = arr.contains(item: 1)',
                 assertion=ContextAssertion(key='a', expected=True)),

            Case(append='a = arr.contains(item: 11000)',
                 assertion=ContextAssertion(key='a', expected=False)),

            Case(append='arr.remove(item: 3)',
                 assertion=ContextAssertion(
                     key='arr', expected=[1, 2, 2, 3, 4, 4, 5, 5])),

            Case(append='a = arr.remove(item: 3)',
                 assertion=ContextAssertion(
                     key='a', expected=[1, 2, 2, 4, 4, 5, 5])),

            Case(append='arr.remove(item: 30)',
                 assertion=ContextAssertion(
                     key='arr', expected=[1, 2, 2, 3, 4, 4, 5, 5])),

            Case(append='a = arr.remove(item: 30)',
                 assertion=ContextAssertion(
                     key='a', expected=[1, 2, 2, 3, 4, 4, 5, 5])),

            Case(append='arr.replace(item: 3 by: 42)',
                 assertion=ContextAssertion(
                     key='arr', expected=[1, 2, 2, 42, 4, 4, 5, 5])),

            Case(append='arr.replace(item: 6 by: 42)',
                 assertion=ContextAssertion(
                     key='arr', expected=[1, 2, 2, 3, 4, 4, 5, 5])),

            Case(append='arr.replace(item: 2 by: 42)',
                 assertion=ContextAssertion(
                     key='arr', expected=[1, 42, 42, 3, 4, 4, 5, 5])),
        ]),
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
                append='while i < 2000000\n'
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
    Suite(
        preparation_lines='i = 0',
        cases=[
            Case(
                append='while true\n'
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
async def test_mutation(suite: Suite, logger):
    """
    How these test suites run:
    Each test suite contains a set of Storyscript lines. Each suite
    also contains multiple cases. For each of these cases, in a test
    suite, we combine the lines of the test suite (which are required
    for preparing context, etc) with the line in this test case. This
    produces a valid tree. Then, we just run this using Lexicon (no mocking).
    After the run completes, we check what kind of assertion we have
    (each test case can have a different kind of assertion).

    This way, we can test the actual execution of the story. This works very
    well for simple stories. Don't run services or anything here. Use it
    to test mutations, variable assignments, value resolution, and so on.
    """
    await run_suite(suite, logger)


async def run_suite(suite: Suite, logger):
    for case in suite.cases:
        await run_test_case_in_suite(suite, case, logger)


async def run_test_case_in_suite(suite: Suite, case: Case, logger):
    File.init()
    Log.init()
    Http.init()
    Json.init()
    story_name = 'dummy_name'

    # Combine the preparation lines with those of the test case.
    all_lines = suite.preparation_lines

    if case.append is not None:
        all_lines = all_lines + '\n' + case.append

    if case.prepend is not None:
        all_lines = case.prepend + '\n' + all_lines

    story = storyscript.Api.loads(all_lines, features={'globals': True})
    errors = story.errors()
    if len(errors) > 0:
        print(f'Failed to compile the following story:'
              f'\n\n{all_lines}', file=sys.stderr)
        raise errors[0]

    app = MagicMock()

    tmp_dir = tempfile.TemporaryDirectory()

    def get_tmp_dir():
        return tmp_dir.name

    app.get_tmp_dir = get_tmp_dir

    app.stories = {
        story_name: story.result().output()
    }
    app.environment = {}

    context = {}

    story = Story(app, story_name, logger)
    story.prepare(context)
    try:
        await Stories.execute(logger, story)
    except StoryscriptError as story_error:
        try:
            assert isinstance(case.assertion, RuntimeExceptionAssertion)
            case.assertion.verify(story_error, context)
        except BaseException as e:
            print(f'Failed to assert exception for the following story:'
                  f'\n\n{all_lines}', file=sys.stderr)
            print(story_error)
            raise e
        return
    except BaseException as e:
        print(f'Failed to run the following story:'
              f'\n\n{all_lines}', file=sys.stderr)
        raise e

    if type(case.assertion) == list:
        assertions = case.assertion
    else:
        assertions = [case.assertion]

    for a in assertions:
        try:
            a.verify(context)
        except BaseException as e:
            print(f'Assertion failure ({type(a)}) for story: \n{all_lines}')
            raise e


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
async def test_arrays(suite, logger):
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
        preparation_lines='foo = 2\n'
                          'zero = 0\n'
                          'a = 2 * 4 / (4 * foo) + 1 * 20 + zero',
        cases=[
            Case(assertion=ContextAssertion(key='a', expected=21))
        ]
    ),
    Suite(
        preparation_lines='a = {} as Map[any,int]\n',
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
        preparation_lines='a = {"a": 1, "b": {} as Map[string,string],'
                          ' "c": 3}\n'
                          'b = ["a", "b", "c"]\n'
                          'c = 1',
        cases=[
            Case(
                append='a[b[c]][c] = -1',
                assertion=ContextAssertion(key='a',
                                           expected={
                                               'a': 1, 'b': {1: -1}, 'c': 3
                                           })
            )
        ]
    ),
    Suite(
        preparation_lines='l = [1, 2, 3]\n'
                          'foreach l as el\n'
                          '  c = [4, 5, 6]\n'
                          '  a = [1, 2, 3]\n'
                          '  c[a[0]] = 1\n',
        cases=[
            Case(
                assertion=ContextAssertion(key='c',
                                           expected=[4, 1, 6])
            )
        ]
    )
])
@mark.asyncio
async def test_resolve_expressions(suite: Suite, logger):
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
async def test_resolve_all_objects(suite: Suite, logger):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        cases=[
            Case(append='a = [0] as List[int]',
                 assertion=ContextAssertion(key='a', expected=[0])),
            Case(append='a = [] as List[int]',
                 assertion=ContextAssertion(key='a', expected=[])),
            Case(append='a = ["3", "2"] as List[int]',
                 assertion=ContextAssertion(key='a', expected=[3, 2])),
            Case(append='a = 2 as float',
                 assertion=ContextAssertion(key='a', expected=2.)),
            Case(append='a = 2.5 as int',
                 assertion=ContextAssertion(key='a', expected=2)),
            Case(append='a = 2 as string',
                 assertion=ContextAssertion(key='a', expected='2')),
            Case(append='a = {2: "42"} as Map[float,float]',
                 assertion=ContextAssertion(key='a', expected={2.: 42.})),
            Case(append='a = "foo" as regex',
                 assertion=ContextAssertion(key='a',
                                            expected=re.compile('foo'))),
            Case(append='a = /foo/ as regex',
                 assertion=ContextAssertion(key='a',
                                            expected=re.compile('foo'))),
            Case(append='a = 2 as any',
                 assertion=ContextAssertion(key='a', expected=2)),
            Case(append='a = true as int',
                 assertion=ContextAssertion(key='a', expected=1)),
            Case(append='a = false as int',
                 assertion=ContextAssertion(key='a', expected=0)),
            Case(append='a = {"foo": 42} as Map[string,int]',
                 assertion=ContextAssertion(key='a',
                                            expected={'foo': 42})),
            Case(append='a = {} as Map[int,boolean]',
                 assertion=ContextAssertion(key='a',
                                            expected={}))
        ]
    ),
    Suite(
        preparation_lines='arr = [] as List[any]\narr.append(item: 42)\n'
                          'b = arr[0]',
        cases=[
            Case(append='c = b as List[int]',
                 assertion=RuntimeExceptionAssertion(
                     TypeAssertionRuntimeError,
                     message='Incompatible type assertion: Received 42 '
                             '(int), but expected List[int]')),
            Case(append='c = b as Map[int,string]',
                 assertion=RuntimeExceptionAssertion(
                     TypeAssertionRuntimeError,
                     message='Incompatible type assertion: Received 42 '
                             '(int), but expected Map[int,string]')),
            Case(append='b=/foo/\nc = b as List[int]',
                 assertion=RuntimeExceptionAssertion(
                     TypeAssertionRuntimeError,
                     message='Incompatible type assertion: Received /foo/ '
                             '(regexp), but expected List[int]')),
        ]
    ),
    Suite(
        cases=[
            Case(append='c = "foo" as float',
                 assertion=RuntimeExceptionAssertion(
                     TypeValueRuntimeError,
                     message='Type conversion failed from str to float '
                             'with `foo`')),
            Case(append='c = "foo" as int',
                 assertion=RuntimeExceptionAssertion(
                     TypeValueRuntimeError,
                     message='Type conversion failed from str to int '
                             'with `foo`')),
            Case(append='c = "foo" as string',
                 assertion=ContextAssertion(key='c', expected='foo')),
            Case(append='c = "10" as int',
                 assertion=ContextAssertion(key='c', expected=10)),
            Case(append='c = "10.1" as float',
                 assertion=ContextAssertion(key='c', expected=10.1)),
        ]
    )
])
@mark.asyncio
async def test_type_casts(suite: Suite, logger):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        preparation_lines='a = [1, 2, 3, 4, 5]',
        cases=[
            Case(append='c=a[0]\nb = a[:2]',
                 assertion=ContextAssertion(key='b', expected=[1, 2])),
            Case(append='b = a[1:2]',
                 assertion=ContextAssertion(key='b', expected=[2])),
            Case(append='b = a[3:]',
                 assertion=ContextAssertion(key='b', expected=[4, 5])),
            Case(append='b = a[10:]',
                 assertion=ContextAssertion(key='b', expected=[])),
            Case(append='b = a[10:20]',
                 assertion=ContextAssertion(key='b', expected=[])),
            Case(append='b = a[:-2]',
                 assertion=ContextAssertion(key='b', expected=[1, 2, 3])),
            Case(append='b = a[-2:5]',
                 assertion=ContextAssertion(key='b', expected=[4, 5])),
            Case(append='c=1\nd=3\nb = a[c:d]',
                 assertion=ContextAssertion(key='b', expected=[2, 3])),
        ]
    ),
    Suite(
        preparation_lines='a = "abcde"',
        cases=[
            Case(append='b = a[:2]',
                 assertion=ContextAssertion(key='b', expected='ab')),
            Case(append='b = a[1:2]',
                 assertion=ContextAssertion(key='b', expected='b')),
            Case(append='b = a[3:]',
                 assertion=ContextAssertion(key='b', expected='de')),
            Case(append='b = a[10:]',
                 assertion=ContextAssertion(key='b', expected='')),
            Case(append='b = a[10:20]',
                 assertion=ContextAssertion(key='b', expected='')),
            Case(append='b = a[:-2]',
                 assertion=ContextAssertion(key='b', expected='abc')),
            Case(append='b = a[-2:5]',
                 assertion=ContextAssertion(key='b', expected='de')),
            Case(append='c=1\nd=3\nb = a[c:d]',
                 assertion=ContextAssertion(key='b', expected='bc')),
        ]
    )
])
@mark.asyncio
async def test_range_mutations(suite: Suite, logger):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(
        cases=[
            Case(
                append='a = 1.23\nb = a.round()',
                assertion=ContextAssertion(key='b', expected=1)
            ),
            Case(
                append='a = 1.56\nb = a.round()',
                assertion=ContextAssertion(key='b', expected=2)
            ),
            Case(
                append='a = 2.22\nb = a.ceil()',
                assertion=ContextAssertion(key='b', expected=3)
            ),
            Case(
                append='a = 4.00\nb = a.ceil()',
                assertion=ContextAssertion(key='b', expected=4)
            ),
            Case(
                append='a = 5.01\nb = a.floor()',
                assertion=ContextAssertion(key='b', expected=5)
            ),
            Case(
                append=f'a = ({math.pi}/2)\nb = a.sin()',
                assertion=ContextAssertion(key='b', expected=1)
            ),
            Case(
                append=f'a = {math.pi}\nb = a.cos()',
                assertion=ContextAssertion(key='b', expected=-1)
            ),
            Case(
                append='a = 0.0\nb = a.tan()',
                assertion=ContextAssertion(key='b', expected=0)
            ),
            Case(
                append='a = 1.0\nb = a.asin()',
                assertion=ContextAssertion(key='b', expected=math.pi / 2)
            ),
            Case(
                append='a = 0.0\nb = a.acos()',
                assertion=ContextAssertion(key='b', expected=math.pi / 2)
            ),
            Case(
                append='a = 0.0\nb = a.atan()',
                assertion=ContextAssertion(key='b', expected=0)
            ),
            Case(
                append=f'a = {math.e}\nb = a.log()',
                assertion=ContextAssertion(key='b', expected=1)
            ),
            Case(
                append='a = 4.0\nb = a.log2()',
                assertion=ContextAssertion(key='b', expected=2)
            ),
            Case(
                append='a = 1000.0\nb = a.log10()',
                assertion=ContextAssertion(key='b', expected=3)
            ),
            Case(
                append='a = 1.0\nb = a.exp()',
                assertion=ContextAssertion(key='b', expected=math.e)
            ),
            Case(
                append='a = -1.0\nb = a.abs()',
                assertion=ContextAssertion(key='b', expected=1)
            ),
            Case(
                append='a = "nan" as float\nb = a.isNaN()',
                assertion=ContextAssertion(key='b', expected=True)
            ),
            Case(
                append='a = "inf" as float\nb = a.isInfinity()',
                assertion=ContextAssertion(key='b', expected=True)
            ),
            Case(
                append=f'a = {math.pi / 4}\n'
                       'b = a.tan()\n'
                       'c = b.approxEqual(value: 1)',
                assertion=ContextAssertion(key='c', expected=True)
            ),
            Case(
                append='a = 1.00\nb = a.approxEqual(value: 2)',
                assertion=ContextAssertion(key='b', expected=False)
            ),
            Case(
                append='a = 1.000001\nb = a.approxEqual(value: 1.000002)',
                assertion=ContextAssertion(key='b', expected=False)
            ),
            Case(
                append='a = 100.0\n'
                       'b = 200.0\n'
                       'c = b.approxEqual(value: a maxRelDiff: 0.5)',
                assertion=ContextAssertion(key='c', expected=True)
            ),
            Case(
                append='a = 100.0\n'
                       'b = 200.0\n'
                       'c = b.approxEqual(value: a maxRelDiff: 0.49)',
                assertion=ContextAssertion(key='c', expected=False)
            ),
            Case(
                append='a = 100.0\n'
                       'b = 200.0\n'
                       'c = b.approxEqual(value: a maxAbsDiff: 100)',
                assertion=ContextAssertion(key='c', expected=True)
            ),
            Case(
                append='a = 100.0\n'
                       'b = 200.0\n'
                       'c = b.approxEqual(value: a maxAbsDiff: 99)',
                assertion=ContextAssertion(key='c', expected=False)
            ),
            Case(
                append=f'a = {math.pi / 4}\n'
                       'b = a.tan()\n'
                       'c = b.approxEqual(value: 1)',
                assertion=ContextAssertion(key='c', expected=True)
            ),
            Case(
                append='a = 1.000001\n'
                       'b = a.approxEqual('
                       '        value: 1.000002'
                       '        maxRelDiff: 0.000001'
                       '        maxAbsDiff: 0'
                       '    )',
                assertion=ContextAssertion(key='b', expected=True)
            ),
            Case(
                append=f'a = 4.0\nb = a.sqrt()',
                assertion=ContextAssertion(key='b', expected=2)
            ),
        ]
    )
])
@mark.asyncio
async def test_float_mutations(suite: Suite, logger):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
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
          ]
          )
])
@mark.asyncio
async def test_try_catch(suite: Suite, logger):
    await run_suite(suite, logger)
