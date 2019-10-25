# -*- coding: utf-8 -*-
from pytest import mark

from .Assertions import (
    Assertion,
    ContextAssertion,
    IsANumberAssertion,
    ListItemAssertion,
    MapValueAssertion,
    RuntimeExceptionAssertion,
)
from .Entities import Case, Suite


@mark.parametrize(
    "suite",
    [
        Suite(
            preparation_lines="function mutate_inputs a: Map[int, int]\n"
            "  a[2] = 2\n"
            "\n"
            "my_map = {1: 1}\n"
            "mutate_inputs(a: my_map)",
            cases=[
                Case(assertion=ContextAssertion(key="my_map", expected={1: 1}))
            ],
        )
    ],
)
@mark.asyncio
async def test_call_by_value(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)
