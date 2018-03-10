# -*- coding: utf-8 -*-
import json

from asyncy.Config import Config
from asyncy.Logger import Logger

from pytest import fixture

import requests


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
    """
    Reads a json and pretend it's an actual response from the api
    """
    def api_response(request_name):
        response = None
        mock_file = 'tests/integration/requests/{}'.format(request_name)
        with open(mock_file, 'r') as f:
            response = json.load(f)
        return response
    return api_response


@fixture
def patch_request(patch, magic, api_response):
    # NOTE(vesuvium): there's no simple way to run an http server and
    # have it return a specific response within testing, so requests is mocked
    def patch_request(request_name):
        mocked_response = api_response(request_name)
        response = magic(json=magic(return_value=mocked_response))
        patch.object(requests, 'get', return_value=response)
    return patch_request
