# -*- coding: utf-8 -*-
import json

from asyncy.Config import Config
from asyncy.Logger import Logger

from pytest import fixture


@fixture
def config():
    return Config()


@fixture
def logger(config):
    logger = Logger(config)
    logger.start()
    return logger


@fixture
def api_response():
    # NOTE(vesuvium): there's no simple way to run an http server and
    # have it return a specific response within testing, so requests is mocked
    response = None
    with open('tests/integration/hello.story.json', 'r') as f:
        response = json.load(f)
    return response
