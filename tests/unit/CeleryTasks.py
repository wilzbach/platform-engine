# -*- coding: utf-8 -*-
from asyncy.CeleryApp import CeleryApp
from asyncy.CeleryTasks import app, config, logger, process_story
from asyncy.Logger import Logger
from asyncy.processing import Story

from pytest import fixture


@fixture
def run(patch):
    patch.object(Story, 'run')


@fixture
def kwargs():
    return {'story_id': None, 'block': None, 'environment': None,
            'context': None}


def test_celerytasks_logger():
    assert isinstance(logger, Logger)


def test_celerytasks_run(patch, run, kwargs):
    patch.many(logger, ['adapt', 'log'])
    process_story('app_id', 'name.story')
    logger.adapt.assert_called_with('app_id', 'name.story')
    logger.log.assert_called_with('task-received', 'app_id', 'name.story')
    args = (config, logger, 'app_id', 'name.story')
    Story.run.assert_called_with(*args, **kwargs)


def test_celerytasks_run_with_story_id(run, kwargs):
    process_story('app_id', 'story_name', story_id=1)
    args = (config, logger, 'app_id', 'story_name')
    kwargs['story_id'] = 1
    Story.run.assert_called_with(*args, **kwargs)


def test_celerytasks_run_block(run, kwargs):
    process_story('app_id', 'story_name', block='parent_line')
    args = (config, logger, 'app_id', 'story_name')
    kwargs['block'] = 'parent_line'
    Story.run.assert_called_with(*args, **kwargs)


def test_celerytasks_run_environment(run, kwargs):
    process_story('app_id', 'story_name', environment={})
    args = (config, logger, 'app_id', 'story_name')
    kwargs['environment'] = {}
    Story.run.assert_called_with(*args, **kwargs)


def test_celerytasks_run_context(run, kwargs):
    process_story('app_id', 'story_name', context={})
    args = (config, logger, 'app_id', 'story_name')
    kwargs['context'] = {}
    Story.run.assert_called_with(*args, **kwargs)
