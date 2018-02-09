# -*- coding: utf-8 -*-
from asyncy.CeleryApp import CeleryApp
from asyncy.CeleryTasks import app, config, logger, process_story
from asyncy.Logger import Logger
from asyncy.tasks import Tasks

from pytest import fixture


@fixture
def run(mocker):
    mocker.patch.object(Tasks, 'run')
    return Tasks.run


def test_celerytasks_logger(mocker):
    assert isinstance(logger, Logger)


def test_celerytasks_run(run):
    process_story('app_id', 'story_name')
    args = (config, logger, 'app_id', 'story_name')
    run.assert_called_with(*args, story_id=None)


def test_celerytasks_run_with_story_id(run):
    process_story('app_id', 'story_name', story_id=1)
    args = (config, logger, 'app_id', 'story_name')
    run.assert_called_with(*args, story_id=1)
