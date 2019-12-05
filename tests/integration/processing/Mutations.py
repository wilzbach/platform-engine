# -*- coding: utf-8 -*-
import math

from pytest import mark

from storyruntime.Exceptions import StoryscriptError, StoryscriptRuntimeError

from .Assertions import (
    ContextAssertion,
    IsANumberAssertion,
    RuntimeExceptionAssertion,
)
from .Entities import Case, Suite


@mark.parametrize(
    "suite",
    [
        Suite(
            preparation_lines="e = 10\n" "o = -3",
            cases=[
                Case(
                    append="a = e.isOdd()",
                    assertion=ContextAssertion(key="a", expected=False),
                ),
                Case(
                    append="a = o.isOdd()",
                    assertion=ContextAssertion(key="a", expected=True),
                ),
                Case(
                    append="a = e.isEven()",
                    assertion=ContextAssertion(key="a", expected=True),
                ),
                Case(
                    append="a = o.isEven()",
                    assertion=ContextAssertion(key="a", expected=False),
                ),
                Case(
                    append="a = o.absolute()",
                    assertion=[
                        ContextAssertion(key="a", expected=3),
                        ContextAssertion(key="o", expected=-3),
                    ],
                ),
                Case(
                    append="a = e.increment()",
                    assertion=[
                        ContextAssertion(key="a", expected=11),
                        ContextAssertion(key="e", expected=10),
                    ],
                ),
                Case(
                    append="a = e.decrement()",
                    assertion=[
                        ContextAssertion(key="a", expected=9),
                        ContextAssertion(key="e", expected=10),
                    ],
                ),
                Case(
                    append="a = e.decrement()",
                    assertion=ContextAssertion(key="e", expected=10),
                ),
                Case(
                    append="a = e.increment()",
                    assertion=ContextAssertion(key="e", expected=10),
                ),
                Case(
                    append="a = e.increment().increment()",
                    assertion=ContextAssertion(key="a", expected=12),
                ),
                Case(
                    append="a = 5.increment().increment()",
                    assertion=ContextAssertion(key="a", expected=7),
                ),
                Case(
                    append="a = -5.increment().increment()",
                    assertion=ContextAssertion(key="a", expected=-3),
                ),
                Case(
                    append="a = (-5).increment().increment()",
                    assertion=ContextAssertion(key="a", expected=-3),
                ),
            ],
        )
    ],
)
@mark.asyncio
async def test_integer_mutations(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize(
    "suite",
    [
        Suite(
            cases=[
                Case(
                    append="a = 1.23\nb = a.round()",
                    assertion=ContextAssertion(key="b", expected=1),
                ),
                Case(
                    append="a = 1.56\nb = a.round()",
                    assertion=ContextAssertion(key="b", expected=2),
                ),
                Case(
                    append="a = 2.22\nb = a.ceil()",
                    assertion=ContextAssertion(key="b", expected=3),
                ),
                Case(
                    append="a = 4.00\nb = a.ceil()",
                    assertion=ContextAssertion(key="b", expected=4),
                ),
                Case(
                    append="a = 5.01\nb = a.floor()",
                    assertion=ContextAssertion(key="b", expected=5),
                ),
                Case(
                    append=f"a = ({math.pi}/2)\nb = a.sin()",
                    assertion=ContextAssertion(key="b", expected=1),
                ),
                Case(
                    append=f"a = {math.pi}\nb = a.cos()",
                    assertion=ContextAssertion(key="b", expected=-1),
                ),
                Case(
                    append="a = 0.0\nb = a.tan()",
                    assertion=ContextAssertion(key="b", expected=0),
                ),
                Case(
                    append="a = 1.0\nb = a.asin()",
                    assertion=ContextAssertion(key="b", expected=math.pi / 2),
                ),
                Case(
                    append="a = 0.0\nb = a.acos()",
                    assertion=ContextAssertion(key="b", expected=math.pi / 2),
                ),
                Case(
                    append="a = 0.0\nb = a.atan()",
                    assertion=ContextAssertion(key="b", expected=0),
                ),
                Case(
                    append=f"a = {math.e}\nb = a.log()",
                    assertion=ContextAssertion(key="b", expected=1),
                ),
                Case(
                    append="a = 4.0\nb = a.log2()",
                    assertion=ContextAssertion(key="b", expected=2),
                ),
                Case(
                    append="a = 1000.0\nb = a.log10()",
                    assertion=ContextAssertion(key="b", expected=3),
                ),
                Case(
                    append="a = 1.0\nb = a.exp()",
                    assertion=ContextAssertion(key="b", expected=math.e),
                ),
                Case(
                    append="a = -1.0\nb = a.abs()",
                    assertion=ContextAssertion(key="b", expected=1),
                ),
                Case(
                    append='a = "nan" to float\nb = a.isNaN()',
                    assertion=ContextAssertion(key="b", expected=True),
                ),
                Case(
                    append='a = "inf" to float\nb = a.isInfinity()',
                    assertion=ContextAssertion(key="b", expected=True),
                ),
                Case(
                    append=f"a = {math.pi / 4}\n"
                    "b = a.tan()\n"
                    "c = b.approxEqual(value: 1)",
                    assertion=ContextAssertion(key="c", expected=True),
                ),
                Case(
                    append="a = 1.00\nb = a.approxEqual(value: 2)",
                    assertion=ContextAssertion(key="b", expected=False),
                ),
                Case(
                    append="a = 1.000001\nb = a.approxEqual(value: 1.000002)",
                    assertion=ContextAssertion(key="b", expected=False),
                ),
                Case(
                    append="a = 100.0\n"
                    "b = 200.0\n"
                    "c = b.approxEqual(value: a maxRelDiff: 0.5)",
                    assertion=ContextAssertion(key="c", expected=True),
                ),
                Case(
                    append="a = 100.0\n"
                    "b = 200.0\n"
                    "c = b.approxEqual(value: a maxRelDiff: 0.49)",
                    assertion=ContextAssertion(key="c", expected=False),
                ),
                Case(
                    append="a = 100.0\n"
                    "b = 200.0\n"
                    "c = b.approxEqual(value: a maxAbsDiff: 100)",
                    assertion=ContextAssertion(key="c", expected=True),
                ),
                Case(
                    append="a = 100.0\n"
                    "b = 200.0\n"
                    "c = b.approxEqual(value: a maxAbsDiff: 99)",
                    assertion=ContextAssertion(key="c", expected=False),
                ),
                Case(
                    append=f"a = {math.pi / 4}\n"
                    "b = a.tan()\n"
                    "c = b.approxEqual(value: 1)",
                    assertion=ContextAssertion(key="c", expected=True),
                ),
                Case(
                    append="a = 1.000001\n"
                    "b = a.approxEqual("
                    "        value: 1.000002"
                    "        maxRelDiff: 0.000001"
                    "        maxAbsDiff: 0"
                    "    )",
                    assertion=ContextAssertion(key="b", expected=True),
                ),
                Case(
                    append=f"a = 4.0\nb = a.sqrt()",
                    assertion=ContextAssertion(key="b", expected=2),
                ),
            ]
        )
    ],
)
@mark.asyncio
async def test_float_mutations(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize(
    "suite",
    [
        Suite(
            preparation_lines='str = "hello world!"',
            cases=[
                Case(
                    append="len = str.length()",
                    assertion=ContextAssertion(key="len", expected=12),
                ),
                Case(
                    append='r = str.contains(item: "hello")',
                    assertion=ContextAssertion(key="r", expected=True),
                ),
                Case(
                    append='r = str.contains(item: "hello1")',
                    assertion=ContextAssertion(key="r", expected=False),
                ),
                Case(
                    append="r = str.contains(pattern: /llo/)",
                    assertion=ContextAssertion(key="r", expected=True),
                ),
                Case(
                    append="r = str.contains(pattern: /f/)",
                    assertion=ContextAssertion(key="r", expected=False),
                ),
                Case(
                    append='parts = str.split(by: " ")',
                    assertion=ContextAssertion(
                        key="parts", expected=["hello", "world!"]
                    ),
                ),
                Case(
                    append='parts = str.split(by: "")',
                    assertion=ContextAssertion(
                        key="parts",
                        expected=[
                            "h",
                            "e",
                            "l",
                            "l",
                            "o",
                            " ",
                            "w",
                            "o",
                            "r",
                            "l",
                            "d",
                            "!",
                        ],
                    ),
                ),
                Case(
                    append="a = str.uppercase()",
                    assertion=ContextAssertion(
                        key="a", expected="HELLO WORLD!"
                    ),
                ),
                Case(
                    append="a = str.lowercase()",
                    assertion=ContextAssertion(
                        key="a", expected="hello world!"
                    ),
                ),
                Case(
                    append="a = str.capitalize()",
                    assertion=ContextAssertion(
                        key="a", expected="Hello World!"
                    ),
                ),
                Case(
                    append="a = str.substring(start: 2)",
                    assertion=ContextAssertion(key="a", expected="llo world!"),
                ),
                Case(
                    append="a = str.substring(start: 2).substring(end: -3)",
                    assertion=ContextAssertion(key="a", expected="llo wor"),
                ),
                Case(
                    append="a = str.substring(end: 5)",
                    assertion=ContextAssertion(key="a", expected="hello"),
                ),
                Case(
                    append="a = str.substring(start: 6 end: 11)",
                    assertion=ContextAssertion(key="a", expected="world"),
                ),
                Case(
                    append="a = str.substring(start: 6 end: -2)",
                    assertion=ContextAssertion(key="a", expected="worl"),
                ),
                Case(
                    append="a = str.substring(start: 6 end: -6)",
                    assertion=ContextAssertion(key="a", expected=""),
                ),
                Case(
                    append="a = str.substring(start: 20)",
                    assertion=ContextAssertion(key="a", expected=""),
                ),
                Case(
                    append="a = str.substring(start: 10 end:20)",
                    assertion=ContextAssertion(key="a", expected="d!"),
                ),
                Case(
                    append="a = str.substring(start: -3)",
                    assertion=ContextAssertion(key="a", expected="ld!"),
                ),
                Case(
                    append='a = str.startswith(prefix: "hello")',
                    assertion=ContextAssertion(key="a", expected=True),
                ),
                Case(
                    append='a = str.startswith(prefix: "ello")',
                    assertion=ContextAssertion(key="a", expected=False),
                ),
                Case(
                    append='a = str.endswith(suffix: "!")',
                    assertion=ContextAssertion(key="a", expected=True),
                ),
                Case(
                    append='a = str.endswith(suffix: ".")',
                    assertion=ContextAssertion(key="a", expected=False),
                ),
            ],
        ),
        Suite(
            preparation_lines='str = "hello."',
            cases=[
                Case(
                    append='r = str.replace(item: "hello" by:"foo")',
                    assertion=ContextAssertion(key="r", expected="foo."),
                ),
                Case(
                    append='r = str.replace(item: "l" by:"o")',
                    assertion=ContextAssertion(key="r", expected="heooo."),
                ),
                Case(
                    append='r = str.replace(item: "k" by:"$")',
                    assertion=ContextAssertion(key="r", expected="hello."),
                ),
                Case(
                    append='r = str.replace(pattern: /hello/ by:"foo")',
                    assertion=ContextAssertion(key="r", expected="foo."),
                ),
                Case(
                    append='r = str.replace(pattern: /l/ by:"o")',
                    assertion=ContextAssertion(key="r", expected="heooo."),
                ),
                Case(
                    append='r = str.replace(pattern: /k/ by:"$")',
                    assertion=ContextAssertion(key="r", expected="hello."),
                ),
            ],
        ),
        Suite(
            preparation_lines='str = " text "',
            cases=[
                Case(
                    append="a = str.trim()",
                    assertion=ContextAssertion(key="a", expected="text"),
                )
            ],
        ),
        Suite(
            cases=[
                Case(
                    append='a = "fooBar"\n'
                    'b = a.replace(pattern: /bar/i by: "foo")',
                    assertion=ContextAssertion(key="b", expected="foofoo"),
                ),
                Case(
                    append='a = "fooBar\\nmv foo.txt"\n'
                    'b = a.replace(pattern: /Bar.+/s by: "rm")',
                    assertion=ContextAssertion(key="b", expected="foorm"),
                ),
                Case(
                    append='a = "fooBar\\nfoobar"\n'
                    'b = a.replace(pattern: /^foo/m by: "Foo")',
                    assertion=ContextAssertion(
                        key="b", expected="FooBar\nFoobar"
                    ),
                ),
                Case(
                    append='a = "fooBar"\n' "b = a.contains(pattern: /ar/)",
                    assertion=ContextAssertion(key="b", expected=True),
                ),
                Case(
                    append='a = "fooBar"\n' "b = a.contains(pattern: /ar/g)",
                    assertion=RuntimeExceptionAssertion(
                        exception_type=StoryscriptError,
                        message="Failed to apply mutation contains! "
                        "err=Invalid flag combination: `g`",
                    ),
                ),
            ]
        ),
    ],
)
@mark.asyncio
async def test_string_mutations(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize(
    "suite",
    [
        Suite(
            preparation_lines="my_list = [1, 2, 3]",
            cases=[
                Case(
                    append="a = (my_list.length()) + 4",
                    assertion=ContextAssertion(key="a", expected=7),
                ),
                Case(
                    append="a = my_list[0]",
                    assertion=ContextAssertion(key="a", expected=1),
                ),
                Case(
                    append="a = my_list[-1]",
                    assertion=ContextAssertion(key="a", expected=3),
                ),
            ],
        ),
        Suite(
            preparation_lines='status = "opened"\n'
            'tag = "priority"\n'
            'if status == "opened" and '
            '["important", "priority"].contains(item: tag)\n'
            "   a = 1",
            cases=[Case(assertion=ContextAssertion(key="a", expected=1))],
        ),
        Suite(
            preparation_lines="arr = [1, 2, 2, 3, 4, 4, 5, 5]",
            cases=[
                Case(
                    append="actual = arr.index(of: 5)",
                    assertion=ContextAssertion(key="actual", expected=6),
                ),
                Case(
                    append="actual = arr.index(of: 500)",
                    assertion=ContextAssertion(key="actual", expected=-1),
                ),
                Case(
                    append="actual = arr.length()",
                    assertion=ContextAssertion(key="actual", expected=8),
                ),
                Case(
                    append="arr = arr.append(item: 6)",
                    assertion=ContextAssertion(
                        key="arr", expected=[1, 2, 2, 3, 4, 4, 5, 5, 6]
                    ),
                ),
                Case(
                    append="arr = arr.prepend(item: 1)",
                    assertion=ContextAssertion(
                        key="arr", expected=[1, 1, 2, 2, 3, 4, 4, 5, 5]
                    ),
                ),
                Case(
                    append="r = arr.random()",
                    assertion=IsANumberAssertion(key="r"),
                ),
                Case(
                    append="arr = arr.reverse()",
                    assertion=ContextAssertion(
                        key="arr", expected=[5, 5, 4, 4, 3, 2, 2, 1]
                    ),
                ),
                Case(
                    append="arr = arr.sort()",
                    assertion=ContextAssertion(
                        key="arr", expected=[1, 2, 2, 3, 4, 4, 5, 5]
                    ),
                ),
                Case(
                    append="min = arr.min()",
                    assertion=ContextAssertion(key="min", expected=1),
                ),
                Case(
                    append="max = arr.max()",
                    assertion=ContextAssertion(key="max", expected=5),
                ),
                Case(
                    append="sum = arr.sum()",
                    assertion=ContextAssertion(key="sum", expected=26),
                ),
                Case(
                    append="arr = arr.unique()",
                    assertion=ContextAssertion(
                        key="arr", expected=[1, 2, 3, 4, 5]
                    ),
                ),
                Case(
                    append="a = arr.contains(item: 1)",
                    assertion=ContextAssertion(key="a", expected=True),
                ),
                Case(
                    append="a = arr.contains(item: 11000)",
                    assertion=ContextAssertion(key="a", expected=False),
                ),
                Case(
                    append="b = arr.remove(item: 3)",
                    assertion=ContextAssertion(
                        key="arr", expected=[1, 2, 2, 3, 4, 4, 5, 5]
                    ),
                ),
                Case(
                    append="a = arr.remove(item: 3)",
                    assertion=ContextAssertion(
                        key="a", expected=[1, 2, 2, 4, 4, 5, 5]
                    ),
                ),
                Case(
                    append="b = arr.remove(item: 30)",
                    assertion=ContextAssertion(
                        key="arr", expected=[1, 2, 2, 3, 4, 4, 5, 5]
                    ),
                ),
                Case(
                    append="a = arr.remove(item: 30)",
                    assertion=ContextAssertion(
                        key="a", expected=[1, 2, 2, 3, 4, 4, 5, 5]
                    ),
                ),
                Case(
                    append="arr = arr.replace(item: 3 by: 42)",
                    assertion=ContextAssertion(
                        key="arr", expected=[1, 2, 2, 42, 4, 4, 5, 5]
                    ),
                ),
                Case(
                    append="arr = arr.replace(item: 6 by: 42)",
                    assertion=ContextAssertion(
                        key="arr", expected=[1, 2, 2, 3, 4, 4, 5, 5]
                    ),
                ),
                Case(
                    append="arr = arr.replace(item: 2 by: 42)",
                    assertion=ContextAssertion(
                        key="arr", expected=[1, 42, 42, 3, 4, 4, 5, 5]
                    ),
                ),
                Case(
                    append='s = arr.join(sep: "x")',
                    assertion=ContextAssertion(
                        key="s", expected="1x2x2x3x4x4x5x5"
                    ),
                ),
            ],
        ),
        Suite(
            preparation_lines='arr = [{"a": 1, "b": 2}, [1, 2], true, 4, 5d, 3.0]',
            cases=[
                Case(
                    append='s = arr.join(sep: ",")',
                    assertion=ContextAssertion(
                        key="s",
                        expected='{"a": 1, "b": 2},[1, 2],true,4,432000000,3.0',
                    ),
                )
            ],
        ),
    ],
)
@mark.asyncio
async def test_list_mutations(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize(
    "suite",
    [
        Suite(
            preparation_lines="a = [1, 2, 3, 4, 5]",
            cases=[
                Case(
                    append="c=a[0]\nb = a[:2]",
                    assertion=ContextAssertion(key="b", expected=[1, 2]),
                ),
                Case(
                    append="b = a[1:2]",
                    assertion=ContextAssertion(key="b", expected=[2]),
                ),
                Case(
                    append="b = a[3:]",
                    assertion=ContextAssertion(key="b", expected=[4, 5]),
                ),
                Case(
                    append="b = a[10:]",
                    assertion=ContextAssertion(key="b", expected=[]),
                ),
                Case(
                    append="b = a[10:20]",
                    assertion=ContextAssertion(key="b", expected=[]),
                ),
                Case(
                    append="b = a[:-2]",
                    assertion=ContextAssertion(key="b", expected=[1, 2, 3]),
                ),
                Case(
                    append="b = a[-2:5]",
                    assertion=ContextAssertion(key="b", expected=[4, 5]),
                ),
                Case(
                    append="c=1\nd=3\nb = a[c:d]",
                    assertion=ContextAssertion(key="b", expected=[2, 3]),
                ),
            ],
        ),
        Suite(
            preparation_lines='a = "abcde"',
            cases=[
                Case(
                    append="b = a[:2]",
                    assertion=ContextAssertion(key="b", expected="ab"),
                ),
                Case(
                    append="b = a[1:2]",
                    assertion=ContextAssertion(key="b", expected="b"),
                ),
                Case(
                    append="b = a[3:]",
                    assertion=ContextAssertion(key="b", expected="de"),
                ),
                Case(
                    append="b = a[10:]",
                    assertion=ContextAssertion(key="b", expected=""),
                ),
                Case(
                    append="b = a[10:20]",
                    assertion=ContextAssertion(key="b", expected=""),
                ),
                Case(
                    append="b = a[:-2]",
                    assertion=ContextAssertion(key="b", expected="abc"),
                ),
                Case(
                    append="b = a[-2:5]",
                    assertion=ContextAssertion(key="b", expected="de"),
                ),
                Case(
                    append="c=1\nd=3\nb = a[c:d]",
                    assertion=ContextAssertion(key="b", expected="bc"),
                ),
            ],
        ),
    ],
)
@mark.asyncio
async def test_range_mutations(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize(
    "suite",
    [
        Suite(
            preparation_lines='m = {"a": 1, "b": 2}',
            cases=[
                Case(
                    append="s = m.length()",
                    assertion=ContextAssertion(key="s", expected=2),
                ),
                Case(
                    append="s = m.keys()",
                    assertion=ContextAssertion(key="s", expected=["a", "b"]),
                ),
                Case(
                    append="s = m.values()",
                    assertion=ContextAssertion(key="s", expected=[1, 2]),
                ),
                Case(
                    append="s = m.flatten()",
                    assertion=ContextAssertion(
                        key="s", expected=[["a", 1], ["b", 2]]
                    ),
                ),
                Case(
                    append='s = m.remove(key: "a")',
                    assertion=[
                        ContextAssertion(key="s", expected={"b": 2}),
                        ContextAssertion(key="m", expected={"a": 1, "b": 2}),
                    ],
                ),
                Case(
                    append='s = m.remove(key: "c")',
                    assertion=[
                        ContextAssertion(key="s", expected={"a": 1, "b": 2}),
                        ContextAssertion(key="m", expected={"a": 1, "b": 2}),
                    ],
                ),
                Case(
                    append='s = m.get(key: "a" default: 3)',
                    assertion=[
                        ContextAssertion(key="s", expected=1),
                        ContextAssertion(key="m", expected={"a": 1, "b": 2}),
                    ],
                ),
                Case(
                    append='s = m.get(key: "c" default: 42)',
                    assertion=ContextAssertion(key="s", expected=42),
                ),
                Case(
                    append='s = m.contains(key: "d")',
                    assertion=ContextAssertion(key="s", expected=False),
                ),
                Case(
                    append='s = m.contains(key: "a")',
                    assertion=ContextAssertion(key="s", expected=True),
                ),
                Case(
                    append="s = m.contains(value: 3)",
                    assertion=ContextAssertion(key="s", expected=False),
                ),
                Case(
                    append="s = m.contains(value: 1)",
                    assertion=ContextAssertion(key="s", expected=True),
                ),
                Case(
                    append='key = "a"\ns = m[key]',
                    assertion=ContextAssertion(key="s", expected=1),
                ),
            ],
        ),
        Suite(
            preparation_lines="a = {1: null}",
            cases=[
                Case(
                    append="exists = false\n"
                    "if a.contains(key: 1)\n"
                    "    exists = true",
                    assertion=ContextAssertion(key="exists", expected=False),
                )
            ],
        ),
        Suite(
            preparation_lines='a = {"key_1": "val_1"}',
            cases=[
                Case(
                    append='b = a["foo"]',
                    assertion=RuntimeExceptionAssertion(
                        exception_type=StoryscriptRuntimeError
                    ),
                ),
                Case(
                    append='b = a.get(key: "foo" default: "def_val")',
                    assertion=ContextAssertion(key="b", expected="def_val"),
                ),
                Case(
                    append='b = a.get(key: "foo" default: null)',
                    assertion=ContextAssertion(key="b", expected=None),
                ),
                Case(
                    append='b = a.get(key: "key_1" default: null)',
                    assertion=ContextAssertion(key="b", expected="val_1"),
                ),
                Case(
                    append='b = a["key_1"]',
                    assertion=ContextAssertion(key="b", expected="val_1"),
                ),
            ],
        ),
    ],
)
@mark.asyncio
async def test_map_mutations(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)
