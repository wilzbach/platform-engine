# -*- coding: utf-8 -*-
from pytest import fixture

from storyruntime.Story import Story
from storyruntime.utils.Resolver import Resolver


@fixture
def logger(magic):
    return magic()


@fixture
def config(magic):
    return magic()


@fixture
def app(magic):
    app = magic()
    app.story_global_contexts = {}
    return app


@fixture
def story(app, logger):
    return Story(app, 'hello.story', logger)


@fixture
def resolver(story):
    return Resolver(story)
