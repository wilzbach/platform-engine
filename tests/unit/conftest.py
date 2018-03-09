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
def story(config, logger):
    return Stories(config, logger, 1, 'hello.story')
