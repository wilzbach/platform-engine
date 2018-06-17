# -*- coding: utf-8 -*-
import time

from asyncy.Stories import Stories
from asyncy.utils import Dict

from pytest import fixture, mark

from storyscript.resolver import Resolver

from asyncy.constants.LineConstants import LineConstants


def test_stories_init(app, logger, story):
    assert story.app == app
    assert story.name == 'hello.story'
    assert story.logger == logger
    # assert story.tree ==
    assert story.results == {}


def test_stories_line(magic, story):
    story.tree = magic()
    line = story.line('1')
    assert line == story.tree['1']


def test_stories_line_none(magic, story):
    story.tree = magic()
    line = story.line(None)
    assert line is None


def test_stories_sorted_lines(magic, story):
    story.tree = {'1': {}, '2': {}, '21': {}, '3': {}}
    assert story.sorted_lines() == ['1', '2', '3', '21']


def test_stories_first_line(patch, story):
    patch.object(Stories, 'sorted_lines', return_value=['16', '23'])
    story.tree = {'23': {'ln': '23'}, '16': {'ln': '16'}}
    result = story.first_line()
    assert Stories.sorted_lines.call_count == 1
    assert result == '16'


def test_stories_function_line_by_name(patch, story):
    story.tree = {
        '1': {'ln': '1', 'next': '2'},
        '2': {'ln': '2', 'method': 'function', 'function': 'execute'}
    }

    function_line = story.function_line_by_name('execute')
    assert function_line == story.tree['2']


def test_stories_is_command(patch, logger, story):
    story.containers = {LineConstants.service: {'commands': {'command': {}}}}
    argument = {'$OBJECT': 'path', 'paths': ['command']}
    result = story.is_command(LineConstants.service, argument)
    assert result


def test_stories_is_command_no_object(patch, logger, story):
    result = story.is_command(LineConstants.service, 'string')
    assert result is None


def test_stories_is_command_none(patch, logger, story):
    story.containers = {LineConstants.service: {'commands': {'command': {}}}}
    argument = {'$OBJECT': 'string'}
    result = story.is_command(LineConstants.service, argument)
    assert result is None


def test_stories_resolve(patch, logger, story):
    patch.object(Resolver, 'resolve')
    story.context = 'context'
    result = story.resolve('args')
    logger.log.assert_called_with('story-resolve', 'args', 'args')
    assert result == 'args'


def test_stories_resolve_file(patch, story):
    # patch for $OBJECT=file
    patch.object(Resolver, 'resolve', return_value='/file.path')
    story.context = 'context'
    result = story.resolve({'$OBJECT': 'file', 'string': '/file.path'})
    assert result == '/tmp/cache/file.path'


def test_command_arguments_list(patch, story):
    patch.object(Stories, 'resolve', return_value='something')
    obj = {'$OBJECT': 'string', 'string': 'string'}
    result = story.command_arguments_list([obj])
    Stories.resolve.assert_called_with(obj, encode=True)
    assert result == ['something']


def test_command_arguments_list_none(patch, story):
    """
    Ensures that when an argument resolves to None it is used literally
    """
    patch.object(Stories, 'resolve', return_value=None)
    obj = {'$OBJECT': 'path', 'paths': ['literal']}
    result = story.command_arguments_list([obj])
    Stories.resolve.assert_called_with(obj)
    assert result == ['literal']


def test_stories_resolve_command(patch, logger, story):
    patch.many(Stories, ['is_command', 'command_arguments_list'])
    Stories.command_arguments_list.return_value = ['argument']
    line = {LineConstants.service: LineConstants.service, 'args': [{'paths': ['command']}, 'arg']}
    result = story.resolve_command(line)
    Stories.is_command.assert_called_with(LineConstants.service, {'paths': ['command']})
    assert result == 'command argument'


def test_stories_resolve_command_http_endpoint(story):
    line = {'container': 'http-endpoint'}
    assert story.resolve_command(line) == 'http-endpoint'


def test_stories_resolve_command_log(patch, logger, story):
    patch.many(Stories, ['is_command', 'command_arguments_list'])
    Stories.command_arguments_list.return_value = ['info', 'message']
    line = {LineConstants.service: 'log',
            'args': [{'$OBJECT': 'path', 'paths': ['info']},
                     {'$OBJECT': 'string', 'string': 'message'}]}
    result = story.resolve_command(line)
    Stories.command_arguments_list.assert_called_with(line['args'])
    story.logger.log_raw.assert_called_with('info', 'message')
    assert result == 'log'


def test_stories_resolve_command_log_single_arg(patch, logger, story):
    patch.many(Stories, ['is_command', 'command_arguments_list'])
    Stories.command_arguments_list.return_value = ['part1', 'part2']
    line = {LineConstants.service: 'log',
            'args': [{'$OBJECT': 'string', 'string': 'part1'},
                     {'$OBJECT': 'string', 'string': 'part2'}]}
    result = story.resolve_command(line)
    Stories.command_arguments_list.assert_called_with(line['args'])
    story.logger.log_raw.assert_called_with('info', 'part1, part2')
    assert result == 'log'


def test_stories_resolve_command_log_single_message(patch, logger, story):
    patch.many(Stories, ['is_command'])
    line = {
        'container': 'log',
        'args': [{'$OBJECT': 'string', 'string': 'part1'}]
    }
    result = story.resolve_command(line)
    story.logger.log_raw.assert_called_with('info', 'part1')
    assert result == 'log'


def test_stories_resolve_command_none(patch, logger, story):
    patch.many(Stories, ['is_command', 'command_arguments_list'])
    Stories.is_command.return_value = None
    line = {LineConstants.service: LineConstants.service, 'args': ['command', 'arg']}
    story.resolve_command(line)
    Stories.command_arguments_list.assert_called_with(line['args'])


def test_stories_start_line(patch, story):
    patch.object(time, 'time')
    story.start_line('1')
    assert story.results['1'] == {'start': time.time()}


def test_stories_end_line(patch, story):
    patch.object(time, 'time')
    story.results = {'1': {'start': 'start'}}
    story.end_line('1')
    assert story.results['1']['output'] is None
    assert story.results['1']['end'] == time.time()
    assert story.results['1']['start'] == 'start'


def test_stories_end_line_output(patch, story):
    patch.object(time, 'time')
    story.results = {'1': {'start': 'start'}}
    story.end_line('1', output='output')
    assert story.results['1']['output'] == 'output'


def test_stories_end_line_output_assign(patch, story):
    patch.object(Dict, 'set')
    story.results = {'1': {'start': 'start'}}
    assign = {'paths': ['x']}
    story.end_line('1', output='output', assign=assign)
    assert story.results['1']['output'] == 'output'
    Dict.set.assert_called_with(story.context, assign['paths'], 'output')


def test_stories_end_line_output_as_list(patch, story):
    patch.object(time, 'time')
    story.results = {'1': {'start': 'start'}}
    story.end_line('1', output=['a', 'b'])
    assert story.results['1']['output'] == ['a', 'b']


def test_stories_end_line_output_as_json(patch, story):
    patch.object(time, 'time')
    story.results = {'1': {'start': 'start'}}
    story.end_line('1', output='{"key":"value"}')
    assert story.results['1']['output'] == {'key': 'value'}


def test_stories_end_line_output_as_sting(patch, story):
    patch.object(time, 'time')
    story.results = {'1': {'start': 'start'}}
    story.end_line('1', output='   foobar\n\t')
    assert story.results['1']['output'] == 'foobar'


def test_stories_end_line_output_as_bytes(patch, story):
    patch.object(time, 'time')
    story.results = {'1': {'start': 'start'}}
    story.end_line('1', output=b'output')
    assert story.results['1']['output'] == 'output'


@mark.parametrize('input,output', [
    (None, 'null'),
    (False, 'false'),
    (True, 'true'),
    ('string', "'string'"),
    ("st'ring", "'st\'ring'"),
    (1, "'1'"),
    ({'foo': 'bar'}, "'{\"foo\": \"bar\"}'"),
    (['foobar'], "'[\"foobar\"]'"),
])
def test_stories_encode(story, input, output):
    assert story.encode(input) == output


def test_stories_argument_by_name_empty(story):
    assert story.argument_by_name({}, 'foo') is None


def test_stories_argument_by_name_lookup(patch, story):
    line = {
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'foo',
                'argument': {'$OBJECT': 'string', 'string': 'bar'}
            }
        ]
    }

    patch.object(story, 'resolve')
    story.argument_by_name(line, 'foo')
    story.resolve.assert_called_with(line['args'][0]['argument'])


def test_stories_argument_by_name_missing(patch, story):
    line = {'args': []}
    assert story.argument_by_name(line, 'foo') is None


def test_stories_prepare(story):
    story.prepare(None)


def test_stories_prepare_context(story, app):
    story.app = app
    context = {}
    story.prepare(context=context)
    assert story.environment == app.environment
    assert story.context == context


def test_stories_next_block_simple(patch, story):
    story.tree = {
        '2': {'ln': '2', 'enter': '3', 'next': '3'},
        '3': {'ln': '3', 'parent': '2', 'next': '4'},
        '4': {'ln': '4'}
    }

    assert isinstance(story, Stories)

    assert story.next_block(story.line('2')) == story.tree['4']


def test_stories_next_block_as_lines(patch, story):
    story.tree = {
        '2': {'ln': '2', 'next': '3'},
        '3': {'ln': '3', 'next': '4'}
    }

    assert isinstance(story, Stories)

    assert story.next_block(story.line('2')) == story.tree['3']


def test_stories_next_block_where_next_block_is_block(patch, story):
    story.tree = {
        '2': {'ln': '2', 'next': '3'},
        '3': {'ln': '3', 'next': '4', 'enter': '4'},
        '4': {'ln': '4', 'parent': '3'}
    }

    assert isinstance(story, Stories)

    assert story.next_block(story.line('2')) == story.tree['3']


def test_stories_context_for_function_call(story):
    assert story.context_for_function_call({}, {}) == {}


def test_stories_context_for_function_call_with_args(story):
    line = {
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'foo',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'bar'
                }
            },
            {
                '$OBJECT': 'argument',
                'name': 'foo1',
                'argument': {
                    '$OBJECT': 'string',
                    'string': 'bar1'
                }
            }
        ]
    }

    function_line = {
        'args': [
            {
                '$OBJECT': 'argument',
                'name': 'foo',
                'argument': {
                    '$OBJECT': 'type',
                    'type': 'string'
                }
            },
            {
                '$OBJECT': 'argument',
                'name': 'foo1',
                'argument': {
                    '$OBJECT': 'type',
                    'type': 'string'
                }
            }
        ]
    }

    assert story.context_for_function_call(line, function_line) == {
        'foo': 'bar',
        'foo1': 'bar1'
    }


def test_stories_next_block_nested(patch, story):
    story.tree = {
        '2': {'ln': '2', 'enter': '3', 'next': '3'},
        '3': {'ln': '3', 'parent': '2', 'next': '4'},
        '4': {'ln': '4', 'enter': '5', 'parent': '2', 'next': '5'},
        '5': {'ln': '5', 'parent': '4', 'next': '6'},
        '6': {'ln': '6', 'parent': '4', 'next': '7'},
        '7': {'ln': '7'}
    }

    assert isinstance(story, Stories)

    assert story.next_block(story.line('2')) == story.tree['7']


def test_stories_next_block_last_line(patch, story):
    story.tree = {
        '2': {'ln': '2', 'enter': '3', 'next': '3'},
        '3': {'ln': '3', 'parent': '2', 'next': '4'},
        '4': {'ln': '4', 'enter': '5', 'parent': '2', 'next': '5'},
        '5': {'ln': '5', 'parent': '4', 'next': '6'},
        '6': {'ln': '6', 'parent': '4'}
    }

    assert isinstance(story, Stories)

    assert story.next_block(story.line('2')) is None


def test_stories_next_block_nested_inner(patch, story):
    story.tree = {
        '2': {'ln': '2', 'enter': '3', 'next': '3'},
        '3': {'ln': '3', 'parent': '2', 'next': '4'},
        '4': {'ln': '4', 'enter': '5', 'parent': '2', 'next': '5'},
        '5': {'ln': '5', 'parent': '4', 'next': '6'},
        '6': {'ln': '6', 'parent': '4', 'next': '7'},
        '7': {'ln': '7', 'parent': '2', 'next': '8'},
        '8': {'ln': '8', 'parent': '2'}
    }

    assert isinstance(story, Stories)

    assert story.tree['7'] == story.next_block(story.line('4'))
