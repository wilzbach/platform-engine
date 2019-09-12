# -*- coding: utf-8 -*-
from pytest import fixture

from storyruntime.Story import Story


@fixture
def logger(magic):
    return magic()


@fixture
def config(magic):
    return magic()


@fixture
def app(magic):
    app = magic()
    app.story_global_context = {}
    return app


@fixture
def story(app, logger):
    return Story(app, 'hello.story', logger)
