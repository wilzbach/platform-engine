# -*- coding: utf-8 -*-
from asyncy.models import BaseModel, Users

from peewee import CharField, IntegerField


def test_users():
    assert isinstance(Users.name, CharField)
    assert isinstance(Users.email, CharField)
    assert isinstance(Users.github_handle, CharField)
    assert isinstance(Users.installation_id, IntegerField)
    assert Users.installation_id.null is True
    assert issubclass(Users, BaseModel)
