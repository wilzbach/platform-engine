# -*- coding: utf-8 -*-
from asyncy.models import Database, db


def test_db():
    assert isinstance(db, Database)
