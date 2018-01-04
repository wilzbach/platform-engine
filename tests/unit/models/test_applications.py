# -*- coding: utf-8 -*-
from evenflow.models import Applications, BaseModel

from peewee import CharField, ForeignKeyField


def test_applications():
    assert isinstance(Applications.name, CharField)
    assert isinstance(Applications.user, ForeignKeyField)
    assert issubclass(Applications, BaseModel)
