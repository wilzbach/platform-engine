# -*- coding: utf-8 -*-
from asyncy.Config import Config
from asyncy.Stories import Stories

from pytest import fixture


@fixture
def magic(mocker):
    """
    Shorthand for mocker.MagicMock. It's magic!
    """
    return mocker.MagicMock


@fixture
def init_patching(mocker):
    """
    Makes patching a class' constructor slightly easier
    """
    def init_patching(item):
        mocker.patch.object(item, '__init__', return_value=None)
    return init_patching


@fixture
def patch_many(mocker):
    """
    Makes patching many attributes of the same object simpler
    """
    def patch_many(item, attributes):
        for attribute in attributes:
            mocker.patch.object(item, attribute)
    return patch_many


@fixture
def patch(mocker, init_patching, patch_many):
    mocker.patch.init = init_patching
    mocker.patch.many = patch_many
    return mocker.patch


@fixture
def logger(magic):
    return magic()


@fixture
def config(mocker):
    return Config()


@fixture
def story(logger):
    return Stories(logger, 1, 'hello.story')
