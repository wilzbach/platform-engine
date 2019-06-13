# -*- coding: utf-8 -*-
from asyncy.Config import Config
from asyncy.Logger import Logger
from asyncy.Stories import Stories

from pytest import fixture

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
def services(app, logger):
    asset_dir = examples.__path__[0]

    with open(asset_dir + '/services.json', 'r') as file:
        return ujson.loads(file.read())


@fixture
def story(app, logger):
    asset_dir = examples.__path__[0]

    with open(asset_dir + '/stories.json', 'r') as file:
        app.stories = ujson.loads(file.read())['stories']
    # assert 0
    return Stories(app, 'hello.story', logger)


@fixture
def raw_stories(app, logger):
    asset_dir = examples.__path__[0]

    with open(asset_dir + '/stories.json', 'r') as file:
        return ujson.loads(file.read())

@fixture
def raw_bad_story(app, logger):
    asset_dir = examples.__path__[0]

    with open(asset_dir + '/stories.json', 'r') as file:
        app.stories = ujson.loads(file.read())['stories']
    return app.stories['broken.story']

@fixture
def bad_story(app, logger):
    asset_dir = examples.__path__[0]

    with open(asset_dir + '/stories.json', 'r') as file:
        app.stories = ujson.loads(file.read())['stories']
    return Stories(app, 'broken.story', logger)


@fixture
def logger(config):
    logger = Logger(config)

    def logger_error(msg, exc=None):
        if exc is not None:
            raise exc

    logger.error = logger_error
    logger.start()
    return logger
