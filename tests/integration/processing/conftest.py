# -*- coding: utf-8 -*-
import sys
import tempfile
from unittest.mock import MagicMock

import pytest

from storyruntime.Exceptions import StoryscriptError
from storyruntime.Story import Story
from storyruntime.processing import Stories
from storyruntime.processing.internal import File, Http, Json, Log

import storyscript

from tests.integration.processing.Assertions import RuntimeExceptionAssertion
from tests.integration.processing.Entities import Case, Suite


@pytest.fixture
def run_suite():
    async def proxy(suite: Suite, logger):
        for case in suite.cases:
            await run_test_case_in_suite(suite, case, logger)
    return proxy


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
    app.story_global_contexts = {}
    app.environment = {}

    story = Story(app, story_name, logger)
    try:
        await Stories.execute(logger, story)
    except StoryscriptError as story_error:
        try:
            assert isinstance(case.assertion, RuntimeExceptionAssertion)
            case.assertion.verify(story_error, story.get_context())
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
            a.verify(story.get_context())
        except BaseException as e:
            print(f'Assertion failure ({type(a)}) for story: \n{all_lines}')
            raise e
