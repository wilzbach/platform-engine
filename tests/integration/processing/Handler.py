# -*- coding: utf-8 -*-
from asyncy.App import App
from asyncy.Config import Config
from asyncy.Containers import Containers

from pytest import fixture, mark


@fixture
def app(magic):
    return magic()


@mark.asyncio
async def test_handler_run(patch, logger, story):
    story.app = App(Config(), logger)
    story.prepare()
    patch.object(Containers, 'format_command', return_value=['pwd'])
    # TODO replacement for this int test

    await Handler.run(logger, '1', story)
