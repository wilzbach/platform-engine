# -*- coding: utf-8 -*-
import os

from asyncy.Yaml import Yaml

from pytest import fixture


@fixture
def string():
    return 'asyncy: true\nstoryscript: 3\n'


@fixture
def teardown():
    def teardown():
        os.remove('file.yml')
    return teardown


@fixture
def yaml_file(request, teardown, string):
    with open('file.yml', 'w') as f:
        f.write(string)
    request.addfinalizer(teardown)


def test_yaml_string(string):
    assert Yaml.string(string) == {'asyncy': True, 'storyscript': 3}


def test_yaml_load(mocker, yaml_file):
    mocker.patch.object(Yaml, 'string')
    assert Yaml.path('file.yml') == Yaml.string()


def test_yaml_load_nofile():
    assert Yaml.path('no.yml') is None
