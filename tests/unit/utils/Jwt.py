# -*- coding: utf-8 -*-
import os
import time

from asyncy.utils import Jwt

import jwt

from pytest import fixture


@fixture
def payload(mocker):
    mocker.patch.object(time, 'time', return_value=1.2)
    return {'iat': int(time.time()), 'exp': int(time.time() + 60)}


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


def test_jwt_encode(mocker, encoder, payload):
    mocker.patch.object(Jwt, 'read_key')
    result = Jwt.encode('secret', 60)
    Jwt.read_key.assert_called_with('secret')
    jwt.encode.assert_called_with(payload, Jwt.read_key(), algorithm='RS256')
    assert result == jwt.encode().decode()


def test_jwt_encode_extra_claims(mocker, encoder, payload):
    mocker.patch.object(Jwt, 'read_key')
    Jwt.encode('secret', 60, claim='claim')
    payload['claim'] = 'claim'
    jwt.encode.assert_called_with(payload, Jwt.read_key(), algorithm='RS256')
