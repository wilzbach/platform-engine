# -*- coding: utf-8 -*-
from asyncy.Stories import Stories
from asyncy.processing import Handler


def test_handler_run_run(logger, config, patch_request):
    patch_request('hello.story.json')
    story = Stories(config, logger, 1, 'hello.story')
    story.get()
    Handler.run(logger, '1', story)


def test_handler_run_set(logger, config, patch_request):
    patch_request('colours.story.json')
    story = Stories(config, logger, 1, 'colours.story')
    story.get()
    Handler.run(logger, '1', story)


def test_handler_run_for(logger, config, patch_request):
    patch_request('attendees.story.json')
    story = Stories(config, logger, 1, 'attendees.story')
    story.get()
    Handler.run(logger, '1', story)


def test_handler_run_wait(logger, config, patch_request):
    patch_request('waiting.story.json')
    story = Stories(config, logger, 1, 'waiting.story')
    story.get()
    Handler.run(logger, '1', story)
