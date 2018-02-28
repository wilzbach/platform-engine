# -*- coding: utf-8 -*-
from asyncy.utils import Http

from pytest import fixture, mark

import requests


@fixture
def requests_mocks(mocker):
    mocker.patch.object(requests, 'get')
    mocker.patch.object(requests, 'post')


@mark.parametrize('method', ['get', 'post'])
def test_http_methods(requests_mocks, method):
    response = getattr(Http, method)('url')
    request_method = getattr(requests, method)
    request_method.assert_called_with('url')
    assert response == request_method().text


@mark.parametrize('method', ['get', 'post'])
def test_http_methods_kwargs(requests_mocks, method):
    response = getattr(Http, method)('url', headers={})
    request_method = getattr(requests, method)
    request_method.assert_called_with('url', headers={})
    assert response == request_method().text


@mark.parametrize('method', ['get', 'post'])
def test_http_get_json(requests_mocks, method):
    response = getattr(Http, method)('url', json=True)
    assert response == getattr(requests, method)().json()
