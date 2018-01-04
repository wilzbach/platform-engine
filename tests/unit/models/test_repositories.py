# -*- coding: utf-8 -*-
from evenflow.models.Base import BaseModel
from evenflow.models.Repositories import Repositories

from peewee import CharField, ForeignKeyField


def test_repositories():
    assert isinstance(Repositories.user, ForeignKeyField)
    assert isinstance(Repositories.name, CharField)
    assert isinstance(Repositories.owner, CharField)
    assert issubclass(Repositories, BaseModel)
