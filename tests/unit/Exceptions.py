# -*- coding: utf-8 -*-
from pytest import mark, raises

from storyruntime.Exceptions import StoryscriptError, TooManyActiveApps, \
    TooManyServices, TooManyVolumes


def test_asyncy_error():
    with raises(StoryscriptError):
        raise StoryscriptError('things happen')


def test_many_volumes():
    with raises(TooManyVolumes):
        raise TooManyVolumes(10, 10)


def test_many_apps():
    with raises(TooManyActiveApps):
        raise TooManyActiveApps(10, 10)


def test_no_trace_available():
    err = StoryscriptError(message='my_message')
    assert str(err) == 'StoryscriptError: my_message'


@mark.parametrize('with_root', [True, False])
@mark.parametrize('long_message', [True, False])
def test_exception_trace(magic, patch, story, with_root, long_message):
    root_message = 'test'
    root = BaseException(root_message)

    if not with_root:
        root = None
        root_message = ''

    patch.object(story, 'get_stack', return_value=['1', '2', '3'])

    patch.object(story, 'line', side_effect=[
        {'src': 'line_3'}, {'method': 'hello'}, {'src': 'line_1'}])

    story.name = 'story_name'

    if long_message:
        message = f'long error {"x" * 250}'
    else:
        message = 'unknown error'

    ex = StoryscriptError(
        message=message, story=story,
        line=magic(), root=root
    )

    # We cache the result of str(ex) because if we don't, __str__ will run
    # again, and will then throw a StopIteration exception since
    # pytest mocks the function `line` above.
    str_version = str(ex)
    if root_message:
        root_message = f': {root_message}'

    if long_message:
        expected_message = f'{message[:125]}...'
    else:
        expected_message = message

    assert str_version == f"""An exception has occurred:
{expected_message}{root_message}
    at line 3: line_3 (in story_name)
    at line 2: method=hello (auto generated frame) (in story_name)
    at line 1: line_1 (in story_name)"""


def test_many_services():
    with raises(TooManyServices):
        raise TooManyServices(10, 10)
