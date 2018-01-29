# -*- coding: utf-8 -*-
from asyncy.models import BaseModel, Repositories

from peewee import CharField, ForeignKeyField


def test_repositories():
    assert isinstance(Repositories.name, CharField)
    assert isinstance(Repositories.organization, CharField)
    assert isinstance(Repositories.owner, ForeignKeyField)
    assert issubclass(Repositories, BaseModel)
