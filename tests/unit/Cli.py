# -*- coding: utf-8 -*-
from asyncy.CeleryTasks import process_story
from asyncy.Cli import Cli

from click.testing import CliRunner

from pytest import fixture


@fixture
def runner():
    return CliRunner()


def test_cli_run(patch, runner):
    patch.object(process_story, 'delay')
    result = runner.invoke(Cli.run, ['story', 'app_id'])
    process_story.delay.assert_called_with('app_id', 'story')
    assert result.exit_code == 0
