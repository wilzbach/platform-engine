# -*- coding: utf-8 -*-
from evenflow.models import BaseModel, db

from peewee import Model, PostgresqlDatabase


def test_db():
    assert isinstance(db, PostgresqlDatabase)


def test_base_model():
    assert issubclass(BaseModel, Model)
