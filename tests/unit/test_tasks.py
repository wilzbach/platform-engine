# -*- coding: utf-8 -*-
from evenflow.Tasks import Tasks

from pytest import raises


def test_process_story():
    result = Tasks.process_story('app_id', 'story_name')
    assert result


def test_process_story_force_keyword():
    with raises(TypeError):
        Tasks.process_story('app_id', 'story_name', 'story_id')


def test_process_story_with_id():
    result = Tasks.process_story('app_id', 'story_name', story_id='story_id')
    assert result
