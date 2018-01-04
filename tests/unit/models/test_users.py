# -*- coding: utf-8 -*-
from evenflow.models import BaseModel, Users

from peewee import CharField


def test_users():
    assert isinstance(Users.name, CharField)
    assert isinstance(Users.email, CharField)
    assert isinstance(Users.github_handle, CharField)
    assert issubclass(Users, BaseModel)
