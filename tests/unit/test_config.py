# -*- coding: utf-8 -*-
import os

from evenflow.Config import Config

from pytest import fixture


@fixture
def config():
    Config.defaults['value'] = 'potatoes'
    return Config


def test_config():
    database_url = 'postgresql://postgres:postgres@localhost:5432/database'
    broker_url = 'amqp://:@localhost:5672/'
    assert Config.defaults['database'] == database_url
    assert Config.defaults['mongo'] == 'mongodb://localhost:27017/'
    assert Config.defaults['broker'] == broker_url
    assert Config.defaults['github.pem_path'] == 'github.pem'
    assert Config.defaults['github.app_identifier'] == '123456789'


def test_config_get(mocker, config):
    mocker.patch.object(os, 'getenv', return_value='myvalue')
    result = config.get('value')
    os.getenv.assert_called_with('value', default=config.defaults['value'])
    assert result == 'myvalue'


def test_config_get_invalid():
    assert Config.get('strawberries') is None
