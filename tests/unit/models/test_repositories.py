# -*- coding: utf-8 -*-
from evenflow.models import BaseModel, Repositories

from peewee import CharField, ForeignKeyField


def test_repositories():
    assert isinstance(Repositories.user, ForeignKeyField)
    assert isinstance(Repositories.name, CharField)
    assert isinstance(Repositories.owner, CharField)
    assert issubclass(Repositories, BaseModel)
