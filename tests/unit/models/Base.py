# -*- coding: utf-8 -*-
from asyncy.models import BaseModel

from peewee import Model


def test_base_model():
    assert issubclass(BaseModel, Model)
