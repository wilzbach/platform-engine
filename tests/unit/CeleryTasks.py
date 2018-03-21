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
    patch.many(logger, ['adapt', 'log'])
    process_story('app_id', 'name.story')
    logger.adapt.assert_called_with('app_id', 'name.story')
    logger.log.assert_called_with('task-received', 'app_id', 'name.story')
    args = (config, logger, 'app_id', 'name.story')
    kwargs = {'story_id': None, 'block': None, 'environment': None}
    Story.run.assert_called_with(*args, **kwargs)


def test_celerytasks_run_with_story_id(run):
    process_story('app_id', 'story_name', story_id=1)
    args = (config, logger, 'app_id', 'story_name')
    kwargs = {'story_id': 1, 'block': None, 'environment': None}
    Story.run.assert_called_with(*args, **kwargs)


def test_celerytasks_run_block(run):
    process_story('app_id', 'story_name', block='parent_line')
    args = (config, logger, 'app_id', 'story_name')
    kwargs = {'story_id': None, 'block': 'parent_line', 'environment': None}
    Story.run.assert_called_with(*args, **kwargs)


def test_celerytasks_run_environment(run):
    process_story('app_id', 'story_name', environment={})
    args = (config, logger, 'app_id', 'story_name')
    kwargs = {'story_id': None, 'block': None, 'environment': {}}
    Story.run.assert_called_with(*args, **kwargs)
