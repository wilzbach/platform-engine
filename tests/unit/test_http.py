# -*- coding: utf-8 -*-
import base64

from evenflow.Http import Http

from pytest import fixture, mark

import requests


@fixture
def requests_mocks(mocker):
    mocker.patch.object(requests, 'get')
    mocker.patch.object(requests, 'post')


@fixture
def b64decode(mocker):
    mocker.patch.object(base64, 'b64decode')
    return base64.b64decode


@mark.parametrize('method', ['get', 'post'])
def test_http_methods(requests_mocks, method):
    response = getattr(Http, method)('url')
    request_method = getattr(requests, method)
    request_method.assert_called_with('url')
    assert request_method().raise_for_status.call_count == 1
    assert response == request_method().text


@mark.parametrize('method', ['get', 'post'])
def test_http_methods_kwargs(requests_mocks, method):
    response = getattr(Http, method)('url', headers={})
    request_method = getattr(requests, method)
    request_method.assert_called_with('url', headers={})
    assert request_method().raise_for_status.call_count == 1
    assert response == request_method().text


@mark.parametrize('method', ['get', 'post'])
def test_http_base64_transformation(b64decode, requests_mocks, method):
    response = getattr(Http, method)('url', transformation='base64')
    request_method = getattr(requests, method)
    b64decode.assert_called_with(request_method().text)
    assert response == b64decode()


@mark.parametrize('method', ['get', 'post'])
def test_http_get_json(requests_mocks, method):
    response = getattr(Http, method)('url', transformation='json')
    assert response == getattr(requests, method)().json()
