# -*- coding: utf-8 -*-
from evenflow.Github import Github
from evenflow.Http import Http
from evenflow.Jwt import Jwt
from evenflow.models import Users

from pytest import fixture, mark


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


def test_get_token(mocker, gh):
    mocker.patch.object(Http, 'post')
    mocker.patch.object(Jwt, 'encode', return_value='token')
    mocker.patch.object(Github, 'make_url')
    result = gh.get_token()
    Jwt.encode.assert_called_with('secret', 500, iss='issuer')
    headers = {'Authorization': 'Bearer token'}
    args = {'transformation': 'json', 'headers': headers}
    Http.post.assert_called_with(Github.make_url(), **args)
    assert result == Http.post()['token']


def test_get_contents(mocker, gh):
    mocker.patch.object(Http, 'get')
    mocker.patch.object(Github, 'make_url')
    mocker.patch.object(Github, 'get_token', return_value='token')
    result = gh.get_contents('org', 'repo', 'file')
    Github.make_url.assert_called_with('repository', 'org', 'repo', 'file')
    headers = {'Authorization': 'Bearer token'}
    Http.get.assert_called_with(Github.make_url(), transformation='base64',
                                params={'ref': None}, headers=headers)
    assert Github.get_token.call_count == 1
    assert result == Http.get()


def test_get_contents_version(mocker, gh):
    mocker.patch.object(Http, 'get')
    mocker.patch.object(Github, 'make_url')
    mocker.patch.object(Github, 'get_token', return_value='token')
    gh.get_contents('org', 'repo', 'file', 'version')
    headers = {'Authorization': 'Bearer token'}
    Http.get.assert_called_with(Github.make_url(), transformation='base64',
                                params={'ref': 'version'}, headers=headers)
