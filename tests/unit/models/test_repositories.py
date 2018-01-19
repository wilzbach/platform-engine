# -*- coding: utf-8 -*-
from evenflow.models import BaseModel, Repositories

from peewee import CharField


def test_repositories():
    assert isinstance(Repositories.name, CharField)
    assert isinstance(Repositories.organization, CharField)
    assert issubclass(Repositories, BaseModel)
