# -*- coding: utf-8 -*-
from evenflow.Github import Github
from evenflow.Http import Http
from evenflow.Jwt import Jwt

from pytest import fixture, mark


@fixture
def gh(user):
    return Github('123456789', 'github.pem')


@fixture
def headers():
    return {'Authorization': 'Bearer token',
            'Accept': 'application/vnd.github.machine-man-preview+json'}


def test_github(user, gh):
    assert gh.api_url == 'https://api.github.com'
    assert gh.github_app == '123456789'
    assert gh.github_pem == 'github.pem'
    assert gh.access_token is None


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


def test_authenticate(mocker, gh, headers):
    mocker.patch.object(Http, 'post')
    mocker.patch.object(Jwt, 'encode', return_value='token')
    mocker.patch.object(Github, 'make_url')
    gh.authenticate('installation_id')
    Jwt.encode.assert_called_with(gh.github_pem, 500, iss=gh.github_app)
    args = {'transformation': 'json', 'headers': headers}
    Http.post.assert_called_with(Github.make_url(), **args)
    assert gh.access_token == Http.post()['token']


def test_get_contents(mocker, gh, headers):
    mocker.patch.object(Http, 'get')
    mocker.patch.object(Github, 'make_url')
    gh.access_token = 'token'
    result = gh.get_contents('org', 'repo', 'file')
    Github.make_url.assert_called_with('repository', 'org', 'repo', 'file')
    Http.get.assert_called_with(Github.make_url(), transformation='base64',
                                params={'ref': None}, headers=headers)
    assert result == Http.get()


def test_get_contents_version(mocker, gh, headers):
    mocker.patch.object(Http, 'get')
    mocker.patch.object(Github, 'make_url')
    gh.access_token = 'token'
    gh.get_contents('org', 'repo', 'file', 'version')
    Http.get.assert_called_with(Github.make_url(), transformation='base64',
                                params={'ref': 'version'}, headers=headers)
