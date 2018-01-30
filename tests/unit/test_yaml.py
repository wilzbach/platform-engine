# -*- coding: utf-8 -*-
import os

from asyncy.Yaml import Yaml

from pytest import fixture


@fixture
def teardown():
    def teardown():
        os.remove('file.yml')
    return teardown


@fixture
def yaml_file(request, teardown):
    content = 'asyncy: true\nstoryscript: 3\n'
    with open('file.yml', 'w') as f:
        f.write(content)
    request.addfinalizer(teardown)


def test_yaml_load(yaml_file):
    assert Yaml.load('file.yml') == {'asyncy': True, 'storyscript': 3}


def test_yaml_load_nofile():
    assert Yaml.load('no.yml') is None
