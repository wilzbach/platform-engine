# -*- coding: utf-8 -*-
from asyncy.Stories import Stories
from asyncy.processing import Handler


def test_handler_run_run(logger, config, patch_request):
    patch_request('hello.story.json')
    story = Stories(config, logger, 1, 'hello.story')
    story.get()
    Handler.run(logger, '1', story)
