# -*- coding: utf-8 -*-
from asyncy.Stories import Stories
from asyncy.processing import Handler


def test_handler_run_run(logger, app, patch_request):
    patch_request('hello.story.json')
    story = Stories(app, 'hello.story', logger)
    Handler.run(logger, '1', story)


def test_handler_run_set(logger, app, patch_request):
    patch_request('colours.story.json')
    story = Stories(app, 'colours.story', logger)
    Handler.run(logger, '1', story)


def test_handler_run_for(logger, app, patch_request):
    patch_request('attendees.story.json')
    story = Stories(app, 'attendees.story', logger)
    Handler.run(logger, '1', story)


def test_handler_run_wait(logger, app, patch_request):
    patch_request('waiting.story.json')
    story = Stories(app, 'waiting.story', logger)
    Handler.run(logger, '1', story)
