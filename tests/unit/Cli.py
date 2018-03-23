# -*- coding: utf-8 -*-
from asyncy.CeleryTasks import process_story
from asyncy.Cli import Cli

from click.testing import CliRunner

from pytest import fixture

import ujson


@fixture
def runner():
    return CliRunner()


@fixture
def kwargs():
    return {'block': None, 'context': None}


def test_cli_run(patch, runner, kwargs):
    patch.object(process_story, 'delay')
    result = runner.invoke(Cli.run, ['story', 'app_id'])
    process_story.delay.assert_called_with('app_id', 'story', **kwargs)
    assert result.exit_code == 0


def test_cli_run_block(patch, runner, kwargs):
    patch.object(process_story, 'delay')
    kwargs['block'] = 'line'
    result = runner.invoke(Cli.run, ['story', 'app_id', '--block', 'line'])
    process_story.delay.assert_called_with('app_id', 'story', **kwargs)
    assert result.exit_code == 0


def test_cli_run_context(patch, runner, kwargs):
    patch.object(ujson, 'loads')
    patch.object(process_story, 'delay')
    kwargs['context'] = ujson.loads()
    result = runner.invoke(Cli.run, ['story', 'app_id', '--context',
                                     '{"varible": "value"}'])
    ujson.loads.assert_called_with('{"varible": "value"}')
    process_story.delay.assert_called_with('app_id', 'story', **kwargs)
    assert result.exit_code == 0
