# -*- coding: utf-8 -*-
import os
import socket

from pytest import fixture

from storyruntime.Config import Config


@fixture
def init(patch):
    patch.object(Config, '__init__', return_value=None)


@fixture
def config():
    return Config()


def test_config():
    assert Config.defaults['LOGGER_NAME'] == 'storyscript'
    assert Config.defaults['LOGGER_LEVEL'] == 'debug'
    assert Config.defaults['ENGINE_HOST'] == socket.gethostname()
    assert Config.defaults['ASYNCY_SYNAPSE_HOST'] == 'synapse'
    assert Config.defaults['ASYNCY_SYNAPSE_PORT'] == 80
    assert Config.defaults['ASYNCY_HTTP_GW_HOST'] == 'gateway'
    assert Config.defaults['POSTGRES_URI'] == \
        'postgres://postgres/asyncy?' \
        'search_path=app_public,app_hidden,app_private,public'
    assert Config.defaults['REPORTING_SENTRY_DSN'] is None
    assert Config.defaults['REPORTING_CLEVERTAP_ACCOUNT'] is None
    assert Config.defaults['REPORTING_CLEVERTAP_PASS'] is None


def test_config_init(patch):
    patch.object(Config, 'apply')
    Config()
    Config.apply.assert_called_with()


def test_config_apply(init):
    config = Config()
    config.defaults = {'one': 'value'}
    config.apply()
    assert config.one == 'value'


def test_config_apply_from_env(patch, init):
    patch.object(os, 'getenv', return_value='envvalue')
    config = Config()
    config.defaults = {'one': 'value'}
    config.apply()
    assert config.one == 'envvalue'


def test_config_attribute_empty(config):
    assert config.option is None
