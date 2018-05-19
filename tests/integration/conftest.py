# -*- coding: utf-8 -*-
import os

from asyncy.App import App
from asyncy.Config import Config
from asyncy.Logger import Logger

from pytest import fixture


@fixture
def config():
    return Config()


@fixture
def app():
    os.environ['ASSET_DIR'] = os.path.join(__dir__, './examples/')
    return App()


@fixture
def logger(config):
    logger = Logger(config)
    logger.start()
    return logger
