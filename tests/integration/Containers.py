# -*- coding: utf-8 -*-
from asyncy.App import App
from asyncy.Containers import Containers

from pytest import mark


@mark.asyncio
async def test_exec(logger, config, story):
    story.app = App(config)
    story.prepare()
    result = await Containers.exec(logger, story, 'alpine', 'pwd')

    assert result == '/'
