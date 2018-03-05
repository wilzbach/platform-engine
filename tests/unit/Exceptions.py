# -*- coding: utf-8 -*-
from asyncy.Exceptions import AsyncyError, GithubAuthError

from pytest import raises


def test_asyncy_error():
    with raises(AsyncyError):
        raise AsyncyError('things happen')


def test_github_auth_error():
    with raises(GithubAuthError):
        raise GithubAuthError('app', 'installation')
