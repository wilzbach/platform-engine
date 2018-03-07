# -*- coding: utf-8 -*-
import os

from asyncy.Config import Config

from pytest import fixture


@fixture
def init(patch):
    patch.object(Config, '__init__', return_value=None)


@fixture
def config():
    return Config()


def test_config():
    broker_url = 'amqp://rabbitmq:@rabbitmq:5672/'
    assert Config.defaults['mongo'] == 'mongodb://mongo:27017/'
    assert Config.defaults['broker'] == broker_url
    assert Config.defaults['logger_name'] == 'asyncy'
    assert Config.defaults['logger_level'] == 'warning'


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
