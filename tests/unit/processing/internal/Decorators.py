# -*- coding: utf-8 -*-
from asyncy.processing.internal.Decorators import Decorators
from asyncy.processing.Services import Services


def test_decorators_create_service(patch):
    patch.object(Services, 'register_internal')

    def my_func():
        pass

    Decorators.create_service('name', 'command', 'arguments',
                              'output_type')(my_func)()

    Services.register_internal.assert_called_with('name', 'command', 'arguments',
                                         'output_type', my_func)
