# -*- coding: utf-8 -*-
from asyncy.App import App
from asyncy.Containers import Containers

from pytest import mark


@mark.asyncio
async def test_exec(logger, config, story, echo_service, echo_line):
    story.app = App(config)
    story.app.services = {
        'services': echo_service
    }
    story.prepare()
    result = await Containers.exec(logger, story, echo_line,
                                   'asyncy--echo', 'echo')

    assert result == 'foo'
