# -*- coding: utf-8 -*-
import base64

from evenflow.Github import Github
from evenflow.models import Users

from pytest import fixture, mark

import requests


@fixture
def user():
    return Users('name', 'email', '@handle')


@fixture
def gh(user):
    return Github(user=user)


def test_github(user, gh):
    assert gh.api_url == 'https://api.github.com'
    assert gh.user is user


def test_github_no_user():
    github = Github()
    assert github.user is None


@mark.parametrize('page, url', [
    ('repository', 'repos/{}/{}/contents'),
    ('installations', 'installations/{}/access_tokens')
])
def test_github_url_repository(gh, page, url):
    expected = '{}{}'.format('https://api.github.com/', url)
    assert gh.url(page) == expected


def test_github_url_none(gh):
    assert gh.url('magic') is None


def test_github_make_url(mocker, gh):
    mocker.patch.object(Github, 'url', return_value='test/{}')
    result = gh.make_url('page', 'argument')
    Github.url.assert_called_with('page')
    assert result == 'test/argument'


def test_get_contents(mocker, gh):
    mocker.patch.object(requests, 'get')
    mocker.patch.object(Github, 'make_url')
    mocker.patch.object(base64, 'b64decode')
    result = gh.get_contents('org', 'repo', 'file')
    Github.make_url.assert_called_with('repository', 'org', 'repo', 'file')
    requests.get.assert_called_with(Github.make_url(), params={'ref': None})
    requests.get().raise_for_status.assert_called_with()
    assert result == base64.b64decode(requests.get().text, altchars=None)
