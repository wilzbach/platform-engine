# -*- coding: utf-8 -*-
from asyncy.CeleryApp import CeleryApp
from asyncy.CeleryTasks import app, logger, run
from asyncy.Logger import Logger
from asyncy.Tasks import Tasks

from pytest import fixture


@fixture
def process_story(mocker):
    mocker.patch.object(Tasks, 'process_story')
    return Tasks.process_story


def test_celerytasks_logger(mocker):
    assert isinstance(logger, Logger)


def test_celerytasks_run(process_story):
    run('app_id', 'story_name')
    args = (logger, 'app_id', 'story_name')
    process_story.assert_called_with(*args, story_id=None)


def test_celerytasks_run_with_story_id(process_story):
    run('app_id', 'story_name', story_id=1)
    args = (logger, 'app_id', 'story_name')
    process_story.assert_called_with(*args, story_id=1)
