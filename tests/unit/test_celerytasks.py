# -*- coding: utf-8 -*-
from evenflow.CeleryApp import CeleryApp
from evenflow.CeleryTasks import app, run
from evenflow.Tasks import Tasks

from pytest import fixture


@fixture
def process_story(mocker):
    mocker.patch.object(Tasks, 'process_story')
    return Tasks.process_story


def test_tasks_app(mocker, process_story):
    mocker.patch.object(CeleryApp, 'start')
    assert app == CeleryApp.start()


def test_tasks_run(process_story):
    run('app_id', 'story_name')
    process_story.assert_called_with('app_id', 'story_name', story_id=None)


def test_tasks_run_with_story_id(process_story):
    run('app_id', 'story_name', story_id=1)
    process_story.assert_called_with('app_id', 'story_name', story_id=1)
