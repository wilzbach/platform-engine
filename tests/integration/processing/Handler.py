# -*- coding: utf-8 -*-
from pytest import fixture

from asyncy.Stories import Stories
from asyncy.processing import Handler


@fixture
def app(magic):
    return magic()


def test_handler_run(logger, app, patch_story):
    story = Stories(app, 'hello.story', logger)
    Handler.run(logger, '1', story)
