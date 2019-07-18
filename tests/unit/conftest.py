# -*- coding: utf-8 -*-
from asyncy.Story import Story

from pytest import fixture


@fixture
def logger(magic):
    return magic()


@fixture
def config(magic):
    return magic()


@fixture
def app(magic):
    return magic()


@fixture
def story(app, logger):
    return Story(app, 'hello.story', logger)
