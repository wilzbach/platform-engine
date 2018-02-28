# -*- coding: utf-8 -*-
from asyncy.Exceptions import GithubAuthError
from asyncy.Github import Github
from asyncy.utils import Http, Jwt

from pytest import fixture, mark, raises


@fixture
def gh(logger, user):
    return Github(logger, '123456789', 'github.pem')


@fixture
def headers():
    return {'Authorization': 'Bearer token',
            'Accept': 'application/vnd.github.machine-man-preview+json'}


def test_github_init(logger, user, gh):
    assert gh.api_url == 'https://api.github.com'
    assert gh.github_app == '123456789'
    assert gh.github_pem == 'github.pem'
    assert gh.access_token is None
    assert gh.logger == logger


@mark.parametrize('page, url', [
    ('contents', 'repos/{}/{}/contents/{}'),
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


def test_github_authenticate(patch, gh, headers):
    patch.object(Http, 'post', return_value={'token': 'token'})
    patch.object(Jwt, 'encode', return_value='token')
    patch.object(Github, 'make_url')
    gh.authenticate('installation_id')
    Jwt.encode.assert_called_with(gh.github_pem, 500, iss=gh.github_app)
    args = {'json': True, 'headers': headers}
    Http.post.assert_called_with(Github.make_url(), **args)
    assert gh.access_token == Http.post()['token']


def test_github_authenticate_error(patch, logger, gh):
    patch.object(Jwt, 'encode')
    patch.object(Http, 'post', return_value={})
    patch.object(Github, 'make_url')
    with raises(GithubAuthError):
        gh.authenticate('id')
    logger.log.assert_called_with('github-autherr', gh.github_app, 'id')


def test_decode_base64(gh):
    assert gh.decode_base64('aGVsbG93b3JsZA==') == 'helloworld'


def test_get_contents(mocker, gh, headers):
    mocker.patch.object(Http, 'get', return_value={'content': 'content'})
    mocker.patch.object(Github, 'make_url')
    mocker.patch.object(Github, 'decode_base64')
    gh.access_token = 'token'
    result = gh.get_contents('org', 'repo', 'file')
    Github.make_url.assert_called_with('contents', 'org', 'repo', 'file')
    Http.get.assert_called_with(Github.make_url(), json=True,
                                params={'ref': None}, headers=headers)
    Github.decode_base64.assert_called_with('content')
    assert result == Github.decode_base64()


def test_get_contents_404(mocker, gh, headers):
    mocker.patch.object(Http, 'get', return_value={})
    mocker.patch.object(Github, 'make_url')
    gh.access_token = 'token'
    result = gh.get_contents('org', 'repo', 'file')
    assert result is None


def test_get_contents_version(mocker, gh, headers):
    mocker.patch.object(Http, 'get')
    mocker.patch.object(Github, 'make_url')
    mocker.patch.object(Github, 'decode_base64')
    gh.access_token = 'token'
    gh.get_contents('org', 'repo', 'file', 'version')
    Http.get.assert_called_with(Github.make_url(), json=True,
                                params={'ref': 'version'}, headers=headers)
