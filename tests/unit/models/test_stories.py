# -*- coding: utf-8 -*-
from evenflow.models.Base import BaseModel
from evenflow.models.Stories import Stories

from peewee import CharField, ForeignKeyField


def test_stories():
    assert isinstance(Stories.filename, CharField)
    assert isinstance(Stories.version, CharField)
    assert isinstance(Stories.repository, ForeignKeyField)
    assert isinstance(Stories.application, ForeignKeyField)
    assert issubclass(Stories, BaseModel)
