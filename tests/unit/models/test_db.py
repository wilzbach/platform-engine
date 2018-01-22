# -*- coding: utf-8 -*-
from evenflow.models import Database, db


def test_db():
    assert isinstance(db, Database)
