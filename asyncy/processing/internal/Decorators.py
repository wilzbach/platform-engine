# -*- coding: utf-8 -*-
from functools import wraps

from ..Services import Services


class Decorators:

    @staticmethod
    def create_service(name, command, arguments=None, output_type=None):

        def decorator(func):
            Services.register_internal(name, command, arguments,
                                       output_type, func)

            @wraps(func)
            def decorated_function(*args, **kwargs):
                return func(*args, **kwargs)
            return decorated_function

        return decorator
