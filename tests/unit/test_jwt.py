# -*- coding: utf-8 -*-
import os
import time

from evenflow.Jwt import Jwt

import jwt

from pytest import fixture


@fixture
def payload(mocker):
    mocker.patch.object(time, 'time')
    return {'iat': time.time(), 'exp': time.time() + 60}


@fixture
def pem_key(request):
    filename = 'key.pem'
    with open(filename, 'w') as file:
        file.write('key')

    def teardown():
        os.remove(filename)
    request.addfinalizer(teardown)

    return filename


@fixture
def encoder(mocker):
    mocker.patch.object(jwt, 'encode')


def test_read_key(pem_key):
    assert Jwt.read_key(pem_key) == 'key'


def test_jwt_encode(encoder, payload):
    result = Jwt.encode('secret', 60)
    jwt.encode.assert_called_with(payload, 'secret', algorithm='RS256')
    assert result == jwt.encode()


def test_jwt_encode_extra_claims(encoder, payload):
    Jwt.encode('secret', 60, claim='claim')
    payload['claim'] = 'claim'
    jwt.encode.assert_called_with(payload, 'secret', algorithm='RS256')
