# -*- coding: utf-8 -*-
from asyncy.Stories import Stories

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
    return Stories(app, 'hello.story', logger)
