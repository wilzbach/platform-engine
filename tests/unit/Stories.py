# -*- coding: utf-8 -*-
import time

from asyncy.Stories import Stories
from asyncy.utils import Http

from storyscript.resolver import Resolver


def test_stories_init(config, logger, story):
    assert story.app_id == 1
    assert story.name == 'hello.story'
    assert story.config == config
    assert story.logger == logger
    assert story.results == {}


def test_stories_get(patch, config, story):
    patch.object(Http, 'get')
    story.get()
    url = 'http://{}/apps/1/stories/hello.story'.format(config.api_url)
    Http.get.assert_called_with(url, json=True)
    assert story.tree == Http.get()['tree']
    assert story.context == Http.get()['context']
    assert story.environment == Http.get()['environment']
    assert story.containers == Http.get()['containers']
    assert story.repository == Http.get()['repository']
    assert story.version == Http.get()['version']


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


def test_stories_is_command_none(patch, logger, story):
    story.containers = {'container': {'commands': {'command': {}}}}
    argument = {'$OBJECT': 'string'}
    result = story.is_command('container', argument)
    assert result is None


def test_stories_resolve(patch, logger, story):
    patch.object(Resolver, 'resolve')
    story.context = 'context'
    result = story.resolve('args')
    Resolver.resolve.assert_called_with('args', story.context)
    logger.log.assert_called_with('story-resolve', 'args', Resolver.resolve())
    assert result == Resolver.resolve()


def test_stories_argument_format_type(story):
    assert story.argument_format_type('anything') == '{}'


def test_stories_argument_format_type_string(story):
    assert story.argument_format_type('string') == '"{}"'


def test_stories_command_arguments_string(patch, story):
    patch.object(Stories, 'argument_format_type', return_value='{}')
    story.containers = {'container': {'commands': {
        'echo': {'args': [{'type': 'anything'}]}}
    }}
    result = story.command_arguments_string('container', 'echo')
    Stories.argument_format_type.assert_called_with('anything')
    assert result == '{}'


def test_command_arguments_list(patch, story):
    patch.object(Stories, 'resolve', return_value='something')
    result = story.command_arguments_list([{'string': 'string'}])
    Stories.resolve.assert_called_with({'string': 'string'})
    assert result == ['something']


def test_stories_resolve_command(patch, logger, story):
    patch.many(Stories, ['is_command', 'command_arguments_list',
                         'command_arguments_string'])
    Stories.command_arguments_string.return_value = '{}'
    Stories.command_arguments_list.return_value = ['argument']
    line = {'container': 'container', 'args': [{'paths': ['command']}, 'arg']}
    result = story.resolve_command(line)
    Stories.is_command.assert_called_with('container', {'paths': ['command']})
    assert result == 'command argument'


def test_stories_resolve_command_none(patch, logger, story):
    patch.many(Stories, ['is_command', 'resolve'])
    Stories.is_command.return_value = None
    line = {'container': 'container', 'args': ['command', 'arg']}
    result = story.resolve_command(line)
    Stories.resolve.assert_called_with(['command', 'arg'])
    assert result == story.resolve()


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


def test_stories_get_environment(story):
    story.environment = {'container': {}}
    assert story.get_environment('container') == {}


def test_stories_get_environment_none(story):
    story.environment = {'container': 'dict'}
    assert story.get_environment('else') == {}


def test_stories_prepare(story):
    story.prepare(None, None, None, None)


def test_stories_prepare_environment(story):
    story.prepare('environment', None, None, None)
    assert story.environment == 'environment'


def test_stories_prepare_context(story):
    story.prepare(None, 'context', None, None)
    assert story.context == 'context'


def test_stories_prepare_start(patch, story):
    patch.object(Stories, 'start_from')
    story.prepare(None, None, 'start', None)
    Stories.start_from.assert_called_with('start')


def test_stories_prepare_block(patch, story):
    patch.object(Stories, 'child_block')
    story.prepare(None, None, None, 'block')
    Stories.child_block.assert_called_with('block')
