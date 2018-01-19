# -*- coding: utf-8 -*-
from evenflow.models import ApplicationsRepositories, BaseModel

from peewee import ForeignKeyField


def test_applicationsrepositories():
    assert isinstance(ApplicationsRepositories.repository, ForeignKeyField)
    assert isinstance(ApplicationsRepositories.application, ForeignKeyField)
    assert issubclass(ApplicationsRepositories, BaseModel)
