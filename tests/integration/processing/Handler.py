# -*- coding: utf-8 -*-
from asyncy.processing import Handler

from pytest import fixture


@fixture
def app(magic):
    return magic()


def test_handler_run(logger, story):
    story.prepare()
    Handler.run(logger, '1', story)
