# -*- coding: utf-8 -*-
from evenflow.models import Users

from pytest import fixture


@fixture
def user():
    return Users('name', 'email', '@handle')
