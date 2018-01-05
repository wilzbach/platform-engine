# -*- coding: utf-8 -*-
import base64

from evenflow.Http import Http

from pytest import fixture

import requests


@fixture
def get(mocker):
    mocker.patch.object(requests, 'get')


@fixture
def post(mocker):
    mocker.patch.object(requests, 'post')


def test_http_get(get):
    response = Http.get('url')
    requests.get.assert_called_with('url')
    assert requests.get().raise_for_status.call_count == 1
    assert response == requests.get().text


def test_http_get_base64(mocker, get):
    mocker.patch.object(base64, 'b64decode')
    response = Http.get('url', transformation='base64')
    base64.b64decode.assert_called_with(requests.get().text)
    assert response == base64.b64decode()


def test_http_get_json(get):
    response = Http.get('url', transformation='json')
    assert response == requests.get().json()


def test_http_post(post):
    response = Http.post('url')
    requests.post.assert_called_with('url')
    assert requests.post().raise_for_status.call_count == 1
    assert response == requests.post().text


def test_http_post_base64(mocker, post):
    mocker.patch.object(base64, 'b64decode')
    response = Http.post('url', transformation='base64')
    base64.b64decode.assert_called_with(requests.post().text)
    assert response == base64.b64decode()


def test_http_post_json(post):
    response = Http.post('url', transformation='json')
    assert response == requests.post().json()
