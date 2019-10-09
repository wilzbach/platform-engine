# -*- coding: utf-8 -*-
from pytest import mark

from .Assertions import Assertion, ContextAssertion, IsANumberAssertion,\
    ListItemAssertion, MapValueAssertion, RuntimeExceptionAssertion
from .Entities import Case, Suite


@mark.parametrize('suite', [
    Suite(preparation_lines='a = [1, 2]\n'
                            'b = {"a": "12", "b": true}',
          cases=[
              Case(append='a.append(item: 3)\n'
                          'a.prepend(item: 0)\n'
                          'a.reverse()\n'
                          'a.sort()\n'
                          'a.unique()\n'
                          'a.remove(item: 1)\n'
                          'a.replace(item: 1 by: 2)',
                   assertion=ContextAssertion(key='a', expected=[1, 2])),
              Case(append='a = a.append(item: 3)',
                   assertion=ContextAssertion(key='a', expected=[1, 2, 3])),
              Case(append='c = a.append(item: 3)',
                   assertion=[ContextAssertion(key='a', expected=[1, 2]),
                              ContextAssertion(key='c', expected=[1, 2, 3])]),
              Case(append='c = a.append(item: 3)',
                   assertion=[ContextAssertion(key='a', expected=[1, 2]),
                              ContextAssertion(key='c', expected=[1, 2, 3])]),
          ]
          )
])
@mark.asyncio
async def test_mutation_lists(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize('suite', [
    Suite(preparation_lines='a = {"a": 12, "b": true}',
          cases=[
              Case(append='a.remove(key: "a")',
                   assertion=ContextAssertion(
                       key='a', expected={'a': 12, 'b': True})),
              Case(append='b = a.remove(key: "b")',
                   assertion=ContextAssertion(key='b', expected={'a': 12}))
          ]
          )
])
@mark.asyncio
async def test_mutation_maps(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)
