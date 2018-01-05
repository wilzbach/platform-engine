# -*- coding: utf-8 -*-
import time

import jwt


class Jwt:

    @staticmethod
    def encode(secret, expiration, **kwargs):
        kwargs['iat'] = time.time()
        kwargs['exp'] = kwargs['iat'] + expiration
        return jwt.encode(kwargs, secret, algorithm='RS256')
