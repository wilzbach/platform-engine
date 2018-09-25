# -*- coding: utf-8 -*-
from pytest import mark

from asyncy.Config import Config
from asyncy.Kubernetes import Kubernetes


@mark.asyncio
async def test_start(story):
    story.app.app_id = 'jude-slack-app90'
    story.app.config = Config()
    await Kubernetes.start(story, None)
