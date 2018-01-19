# -*- coding: utf-8 -*-
from evenflow.models import ApplicationsStories, BaseModel

from peewee import ForeignKeyField


def test_applicationsstories():
    assert isinstance(ApplicationsStories.application, ForeignKeyField)
    assert isinstance(ApplicationsStories.story, ForeignKeyField)
    assert issubclass(ApplicationsStories, BaseModel)
