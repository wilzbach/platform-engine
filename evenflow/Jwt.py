# -*- coding: utf-8 -*-
import time

import jwt


class Jwt:

    @staticmethod
    def read_key(path):
        with open(path, mode='r') as file:
            return file.read()

    @staticmethod
    def encode(secret, expiration, **kwargs):
        kwargs['iat'] = time.time()
        kwargs['exp'] = kwargs['iat'] + expiration
        pem_key = Jwt.read_key(secret)
        return jwt.encode(kwargs, pem_key, algorithm='RS256').decode()
