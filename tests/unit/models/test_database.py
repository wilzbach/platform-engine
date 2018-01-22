# -*- coding: utf-8 -*-
from evenflow.models import database

from peewee import PostgresqlDatabase


def test_database():
    assert isinstance(database, PostgresqlDatabase)
