# -*- coding: utf-8 -*-
from asyncy.CeleryApp import CeleryApp
from asyncy.CeleryTasks import app, config, logger, process_story
from asyncy.Logger import Logger
from asyncy.processing import Story

from pytest import fixture


@fixture
def run(patch):
    patch.object(Story, 'run')


def test_celerytasks_logger():
    assert isinstance(logger, Logger)


def test_celerytasks_run(patch, run):
    patch.object(logger, 'log')
    process_story('app_id', 'story_name')
    logger.log.assert_called_with('task-received', 'app_id', 'story_name')
    args = (config, logger, 'app_id', 'story_name')
    kwargs = {'story_id': None, 'resume_from': None, 'environment': None}
    Story.run.assert_called_with(*args, **kwargs)


def test_celerytasks_run_with_story_id(run):
    process_story('app_id', 'story_name', story_id=1)
    args = (config, logger, 'app_id', 'story_name')
    kwargs = {'story_id': 1, 'resume_from': None, 'environment': None}
    Story.run.assert_called_with(*args, **kwargs)


def test_celerytasks_run_resume(run):
    process_story('app_id', 'story_name', resume_from='line', environment={})
    args = (config, logger, 'app_id', 'story_name')
    kwargs = {'story_id': None, 'resume_from': 'line', 'environment': {}}
    Story.run.assert_called_with(*args, **kwargs)
