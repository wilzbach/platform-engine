# -*- coding: utf-8 -*-
from evenflow.models.Base import BaseModel
from evenflow.models.Users import Users

from peewee import CharField


def test_users():
    assert isinstance(Users.name, CharField)
    assert isinstance(Users.email, CharField)
    assert isinstance(Users.github_handle, CharField)
    assert issubclass(Users, BaseModel)
