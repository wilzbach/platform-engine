# -*- coding: utf-8 -*-
from collections import namedtuple
from unittest.mock import MagicMock

from asyncy.Stories import Stories
from asyncy.processing import Story

import pytest
from pytest import mark

import storyscript

TestSuite = namedtuple('TestSuite', ['preparation_lines', 'cases'])

ContextAssertion = namedtuple('ContextAssertion', ['key', 'expected'])
IsANumberContextAssertion = namedtuple('IsANumberAssertion', ['key'])


class TestCase:
    def __init__(self, append=None, prepend=None, assertion=None,
                 expect_exception=None):
        self.append = append
        self.prepend = prepend
        self.assertion = assertion
        self.expect_exception = expect_exception


@mark.parametrize('suite', [  # See pydoc below for how this runs.
    TestSuite(
        preparation_lines='hello = "hello"\n'
                          'world = "world"',
        cases=[
            TestCase(append='a = hello + world',
                     assertion=ContextAssertion(
                         key='a', expected='helloworld')),
            TestCase(append='a = hello + " " + world',
                     assertion=ContextAssertion(
                         key='a', expected='hello world')),
            TestCase(append='a = hello + " "',  # Test for auto trim.
                     assertion=ContextAssertion(
                         key='a', expected='hello')),
            TestCase(append='a = "{hello}"',
                     assertion=ContextAssertion(
                         key='a', expected='hello')),
            TestCase(append='a = "{hello} {world}"',
                     assertion=ContextAssertion(
                         key='a', expected='hello world')),
            TestCase(append='a = "{hello}{world}"',
                     assertion=ContextAssertion(
                         key='a', expected='helloworld'))
        ]
    ),
    TestSuite(
        preparation_lines='labels = [{"name": "a"}]\n'
                          'found = false',
        cases=[
            TestCase(
                append='foreach labels as label\n'
                       '   if label["name"] == "a" or label["name"] == "b"\n'
                       '        found = true\n'
                       'outside = true',
                assertion=[ContextAssertion(key='found', expected=True),
                           ContextAssertion(key='outside', expected=True)]
            )
        ]
    ),
    TestSuite(
        preparation_lines='a = 1\n'
                          'b = 5\n'
                          'c = null\n',
        cases=[
            TestCase(append='if true or false\n'
                            '   c = "true"',
                     assertion=ContextAssertion(key='c', expected='true')),
            TestCase(append='if false or true\n'
                            '   c = "true"',
                     assertion=ContextAssertion(key='c', expected='true')),
            TestCase(append='if true\n'
                            '   c = "true"',
                     assertion=ContextAssertion(key='c', expected='true')),
            TestCase(append='if false\n'
                            '   c = "wtf"',
                     assertion=ContextAssertion(key='c', expected=None)),
            TestCase(append='if a == 100 or b == 100\n'
                            '   c = "wtf"',
                     assertion=ContextAssertion(key='c', expected=None)),
            TestCase(append='if a == 100 or b == 5\n'
                            '   c = "b"',
                     assertion=ContextAssertion(key='c', expected='b')),
            TestCase(append='if a == 1 or b == 100\n'
                            '   c = "a"',
                     assertion=ContextAssertion(key='c', expected='a')),
            TestCase(append='if a == 1 or b == 5\n'
                            '   c = "a"',
                     assertion=ContextAssertion(key='c', expected='a')),
            TestCase(append='if a == 100 or b == 100 or true\n'
                            '   c = "true"',
                     assertion=ContextAssertion(key='c', expected='true'))
        ]
    ),
    TestSuite(
        preparation_lines='a = [1, 2, 3, 4, 5]\n'
                          'b = []\n'
                          'c = []\n',
        cases=[
            TestCase(append='foreach a as elem\n'
                            '   b append item: elem\n'
                            '   foreach b as elem2\n'
                            '       if elem2 > 1\n'
                            '           break\n'
                            '       c append item: elem2\n',
                     assertion=[
                         ContextAssertion(key='b', expected=[1, 2, 3, 4, 5]),
                         ContextAssertion(key='c', expected=[1, 1, 1, 1, 1])
                     ])
        ]
    ),
    TestSuite(
        preparation_lines='a = [1, 1, 1, 2, 3, 4, 5]\n'
                          'b = 0\n',
        cases=[
            TestCase(append='foreach a as elem\n'
                            '   b = b + elem\n'
                            '   if b == 3\n'
                            '       break',
                     assertion=ContextAssertion(key='b', expected=3))
        ]
    ),
    TestSuite(
        preparation_lines='a = []',
        cases=[
            TestCase(append='b = a[10]',
                     assertion=ContextAssertion(key='b', expected=None))
        ]
    ),
    TestSuite(
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
            TestCase(prepend='colour = "blue"',
                     assertion=[ContextAssertion(key='result',
                                                 expected='blue'),
                                ContextAssertion(key='outside_var',
                                                 expected='executed')]),

            TestCase(prepend='colour = "red"',
                     assertion=[ContextAssertion(key='result',
                                                 expected='red'),
                                ContextAssertion(key='outside_var',
                                                 expected='executed')]),

            TestCase(prepend='colour = "yellow"',
                     assertion=[ContextAssertion(key='result',
                                                 expected='yellow'),
                                ContextAssertion(key='outside_var',
                                                 expected='executed')]),

            TestCase(prepend='colour = "green"',
                     assertion=[ContextAssertion(key='result',
                                                 expected='green'),
                                ContextAssertion(key='outside_var',
                                                 expected='executed')]),

            TestCase(prepend='colour = "pink"',
                     assertion=[ContextAssertion(key='result',
                                                 expected='unknown'),
                                ContextAssertion(key='outside_var',
                                                 expected='executed')])
        ]
    ),
    TestSuite(
        preparation_lines='str = "hello world!"',
        cases=[
            TestCase(append='len = str length',
                     assertion=ContextAssertion(key='len', expected=12)),

            TestCase(append='has = str contains pattern: "hello"',
                     assertion=ContextAssertion(key='has', expected=True)),

            TestCase(append='has = str contains pattern: "hello1"',
                     assertion=ContextAssertion(key='has', expected=False)),

            TestCase(append='parts = str split by: " "',
                     assertion=ContextAssertion(
                         key='parts', expected=['hello', 'world!'])),

            TestCase(append='a = str uppercase',
                     assertion=ContextAssertion(
                         key='a', expected='HELLO WORLD!')),

            TestCase(append='a = str lowercase',
                     assertion=ContextAssertion(
                         key='a', expected='hello world!')),

            TestCase(append='a = str capitalize',
                     assertion=ContextAssertion(
                         key='a', expected='Hello World!'))
        ]
    ),
    TestSuite(
        preparation_lines='e = 10\n'
                          'o = -3',
        cases=[
            TestCase(append='a = e is_odd',
                     assertion=ContextAssertion(key='a', expected=False)),

            TestCase(append='a = o is_odd',
                     assertion=ContextAssertion(key='a', expected=True)),

            TestCase(append='a = e is_even',
                     assertion=ContextAssertion(key='a', expected=True)),

            TestCase(append='a = o is_even',
                     assertion=ContextAssertion(key='a', expected=False)),

            TestCase(append='a = o absolute',
                     assertion=[
                         ContextAssertion(key='a', expected=3),
                         ContextAssertion(key='o', expected=-3)
                     ]),

            TestCase(append='a = e increment',
                     assertion=[
                         ContextAssertion(key='a', expected=11),
                         ContextAssertion(key='e', expected=10)
                     ]),

            TestCase(append='a = e decrement',
                     assertion=[
                         ContextAssertion(key='a', expected=9),
                         ContextAssertion(key='e', expected=10)
                     ]),

            TestCase(append='e decrement',
                     assertion=ContextAssertion(key='e', expected=10)),

            TestCase(append='e increment',
                     assertion=ContextAssertion(key='e', expected=10))
        ]
    ),
    TestSuite(
        preparation_lines='m = {"a": 1, "b": 2}',
        cases=[
            TestCase(append='s = m size',
                     assertion=ContextAssertion(key='s', expected=2)),

            TestCase(append='s = m keys',
                     assertion=ContextAssertion(key='s', expected=['a', 'b'])),

            TestCase(append='s = m values',
                     assertion=ContextAssertion(key='s', expected=[1, 2])),

            TestCase(append='s = m flatten',
                     assertion=ContextAssertion(
                         key='s', expected=[['a', 1], ['b', 2]])),

            TestCase(append='s = m pop key: "a"',
                     assertion=[
                         ContextAssertion(key='s', expected=1),
                         ContextAssertion(key='m', expected={'b': 2})
                     ]),

            TestCase(append='s = m get key: "a"',
                     assertion=[
                         ContextAssertion(key='s', expected=1),
                         ContextAssertion(key='m', expected={'a': 1, 'b': 2})
                     ]),

            TestCase(append='s = m contains key: "d"',
                     assertion=ContextAssertion(key='s', expected=False)),

            TestCase(append='s = m contains key: "a"',
                     assertion=ContextAssertion(key='s', expected=True))
        ]
    ),
    TestSuite(
        preparation_lines='arr = [1, 2, 2, 3, 4, 4, 5, 5]',
        cases=[
            TestCase(append='actual = arr index of: 5',
                     assertion=ContextAssertion(key='actual', expected=6)),

            TestCase(append='actual = arr index of: 500',
                     assertion=ContextAssertion(key='actual', expected=-1)),

            TestCase(append='actual = arr length',
                     assertion=ContextAssertion(key='actual', expected=8)),

            TestCase(append='arr append item: 6',
                     assertion=ContextAssertion(
                         key='arr', expected=[1, 2, 2, 3, 4, 4, 5, 5, 6])),

            TestCase(append='arr prepend item: 1',
                     assertion=ContextAssertion(
                         key='arr', expected=[1, 1, 2, 2, 3, 4, 4, 5, 5])),

            TestCase(append='r = arr random',
                     assertion=IsANumberContextAssertion(key='r')),

            TestCase(append='arr reverse',
                     assertion=ContextAssertion(
                         key='arr', expected=[5, 5, 4, 4, 3, 2, 2, 1])),

            TestCase(append='arr sort',
                     assertion=ContextAssertion(
                         key='arr', expected=[1, 2, 2, 3, 4, 4, 5, 5])),

            TestCase(append='min = arr min',
                     assertion=ContextAssertion(key='min', expected=1)),

            TestCase(append='max = arr max',
                     assertion=ContextAssertion(key='max', expected=5)),

            TestCase(append='sum = arr sum',
                     assertion=ContextAssertion(key='sum', expected=26)),

            TestCase(append='arr unique',
                     assertion=ContextAssertion(
                         key='arr', expected=[1, 2, 3, 4, 5])),

            TestCase(append='a = arr contains item: 1',
                     assertion=ContextAssertion(key='a', expected=True)),

            TestCase(append='a = arr contains item: 11000',
                     assertion=ContextAssertion(key='a', expected=False)),

            TestCase(append='arr remove item: 3',
                     assertion=ContextAssertion(
                         key='arr', expected=[1, 2, 2, 4, 4, 5, 5])),

            TestCase(append='arr remove item: 30',
                     assertion=ContextAssertion(
                         key='arr', expected=[1, 2, 2, 3, 4, 4, 5, 5])),
        ])
])
@mark.asyncio
async def test_mutation(suite: TestSuite, logger):
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


async def run_suite(suite: TestSuite, logger):
    for case in suite.cases:
        await run_test_case_in_suite(suite, case, logger)


async def run_test_case_in_suite(suite: TestSuite, case: TestCase, logger):
    story_name = 'dummy_name'

    # Combine the preparation lines with those of the test case.
    all_lines = suite.preparation_lines

    if case.append is not None:
        all_lines = all_lines + '\n' + case.append

    if case.prepend is not None:
        all_lines = case.prepend + '\n' + all_lines

    tree = storyscript.Api.loads(all_lines)

    app = MagicMock()

    app.stories = {
        story_name: tree
    }
    app.environment = {}

    context = {}

    story = Stories(app, story_name, logger)
    story.prepare(context)
    if case.expect_exception is not None:
        with pytest.raises(case.expect_exception):
            await Story.execute(logger, story)
        return
    else:
        await Story.execute(logger, story)

    if type(case.assertion) == list:
        assertions = case.assertion
    else:
        assertions = [case.assertion]

    for a in assertions:
        if isinstance(a, ContextAssertion):
            assert a.expected == context.get(a.key)
        elif isinstance(a, IsANumberContextAssertion):
            val = context.get(a.key)
            assert type(val) == int or type(val) == float
        else:
            raise Exception('Unknown assertion')


@mark.parametrize('suite', [
    TestSuite(preparation_lines='a = [20, 12, 23]', cases=[
        TestCase(append='a[0] = 100', assertion=ContextAssertion(
            key='a', expected=[100, 12, 23]))
    ]),

    TestSuite(preparation_lines='a = [[20, 12, 23], [-1]]', cases=[
        TestCase(append='a[0][1] = 100\na[1][0] = 10',
                 assertion=ContextAssertion(
                     key='a', expected=[[20, 100, 23], [10]]))
    ])
])
@mark.asyncio
async def test_arrays(suite, logger):
    await run_suite(suite, logger)
