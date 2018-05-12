# -*- coding: utf-8 -*-
import time

from asyncy.Stories import Stories

from pytest import fixture, mark

from storyscript.resolver import Resolver


def test_stories_init(app, logger, story):
    assert story.app == app
    assert story.name == 'hello.story'
    assert story.logger == logger
    # assert story.tree ==
    assert story.results == {}


def test_stories_line(magic, story):
    story.tree = magic()
    line = story.line('1')
    assert line == story.tree['script']['1']


def test_stories_sorted_lines(magic, story):
    story.tree = {'script': {'1': {}, '2': {}, '21': {}, '3': {}}}
    assert story.sorted_lines() == ['1', '2', '3', '21']


def test_stories_first_line(patch, story):
    patch.object(Stories, 'sorted_lines', return_value=['16', '23'])
    story.tree = {'script': {'23': {'ln': '23'}, '16': {'ln': '16'}}}
    result = story.first_line()
    assert Stories.sorted_lines.call_count == 1
    assert result == '16'


def test_stories_next_line(patch, story):
    patch.object(Stories, 'sorted_lines', return_value=['1', '2'])
    story.tree = {'script': {'1': {'ln': '1'}, '2': {'ln': '2'}}}
    result = story.next_line('1')
    assert Stories.sorted_lines.call_count == 1
    assert result == story.tree['script']['2']


def test_stories_next_line_jump(patch, story):
    patch.object(Stories, 'sorted_lines', return_value=['1', '3'])
    story.tree = {'script': {'1': {'ln': '1'}, '3': {'ln': '3'}}}
    assert story.next_line('1') == story.tree['script']['3']


def test_stories_next_line_none(patch, story):
    patch.object(Stories, 'sorted_lines', return_value=['1'])
    story.tree = {'script': {'1': {'ln': '1'}}}
    assert story.next_line('1') is None


def test_stories_start_from(patch, story):
    story.tree = {'script': {
        '1': {'ln': '1'},
        '2': {'ln': '2'}
    }}
    story.start_from('2')
    assert story.tree == {'script': {'2': {'ln': '2'}}}


def test_stories_child_block(patch, story):
    story.tree = {'script': {
        '1': {'ln': '1', 'enter': '2', 'exit': 2},
        '2': {'ln': '2', 'parent': '1'},
        '3': {'ln': '3', 'parent': '1'},
    }}
    story.child_block('1')
    assert story.tree == {'script': {'2': {'ln': '2', 'parent': '1'},
                                     '3': {'ln': '3', 'parent': '1'}}}


def test_stories_is_command(patch, logger, story):
    story.containers = {'container': {'commands': {'command': {}}}}
    argument = {'$OBJECT': 'path', 'paths': ['command']}
    result = story.is_command('container', argument)
    assert result


def test_stories_is_command_no_object(patch, logger, story):
    result = story.is_command('container', 'string')
    assert result is None


def test_stories_is_command_none(patch, logger, story):
    story.containers = {'container': {'commands': {'command': {}}}}
    argument = {'$OBJECT': 'string'}
    result = story.is_command('container', argument)
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
    line = {'container': 'container', 'args': [{'paths': ['command']}, 'arg']}
    result = story.resolve_command(line)
    Stories.is_command.assert_called_with('container', {'paths': ['command']})
    assert result == 'command argument'


def test_stories_resolve_command_log(patch, logger, story):
    patch.many(Stories, ['is_command', 'command_arguments_list'])
    Stories.command_arguments_list.return_value = ['info', 'message']
    line = {'container': 'log',
            'args': [{'$OBJECT': 'path', 'paths': ['info']},
                     {'$OBJECT': 'string', 'string': 'message'}]}
    result = story.resolve_command(line)
    Stories.command_arguments_list.assert_called_with(line['args'])
    story.logger.log_raw.assert_called_with('info', 'message')
    assert result == 'log'


def test_stories_resolve_command_log_single_arg(patch, logger, story):
    patch.many(Stories, ['is_command', 'command_arguments_list'])
    Stories.command_arguments_list.return_value = ['part1', 'part2']
    line = {'container': 'log',
            'args': [{'$OBJECT': 'string', 'string': 'part1'},
                     {'$OBJECT': 'string', 'string': 'part2'}]}
    result = story.resolve_command(line)
    Stories.command_arguments_list.assert_called_with(line['args'])
    story.logger.log_raw.assert_called_with('info', 'part1, part2')
    assert result == 'log'


def test_stories_resolve_command_none(patch, logger, story):
    patch.many(Stories, ['is_command', 'command_arguments_list'])
    Stories.is_command.return_value = None
    line = {'container': 'container', 'args': ['command', 'arg']}
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


def test_stories_prepare(story):
    story.prepare(None, None, None)


def test_stories_prepare_context(story, app):
    story.prepare({}, None, None)
    assert story.context == {'env': app.environment}


def test_stories_prepare_start(patch, story):
    patch.object(Stories, 'start_from')
    story.prepare(None, 'start', None)
    Stories.start_from.assert_called_with('start')


def test_stories_prepare_block(patch, story):
    patch.object(Stories, 'child_block')
    story.prepare(None, None, 'block')
    Stories.child_block.assert_called_with('block')
