# -*- coding: utf-8 -*-
from evenflow.Github import Github
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
