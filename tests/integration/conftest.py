# -*- coding: utf-8 -*-
from pytest import fixture

from storyruntime.Config import Config
from storyruntime.Logger import Logger
from storyruntime.Story import Story

import ujson

from . import examples


@fixture
def config():
    return Config()


@fixture
def app(magic):
    asset_dir = examples.__path__[0]
    app = magic()

    with open(asset_dir + '/services.json', 'r') as file:
        app.services = ujson.loads(file.read())

    return app


@fixture
def story(app, logger):
    asset_dir = examples.__path__[0]

    with open(asset_dir + '/stories.json', 'r') as file:
        app.stories = ujson.loads(file.read())['stories']

    return Story(app, 'hello.story', logger)


@fixture
def logger(config):
    logger = Logger(config)
    logger.start()
    return logger
