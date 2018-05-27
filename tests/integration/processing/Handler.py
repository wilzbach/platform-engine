# -*- coding: utf-8 -*-
from asyncy.App import App
from asyncy.Config import Config
from asyncy.processing import Handler

from pytest import fixture, mark


@fixture
def app(magic):
    return magic()


@mark.asyncio
async def test_handler_run(logger, story):
    story.app = App(Config())
    story.prepare()
    await Handler.run(logger, '1', story)
