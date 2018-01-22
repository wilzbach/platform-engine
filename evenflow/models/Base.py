# -*- coding: utf-8 -*-
from peewee import Model

from .db import db


class BaseModel(Model):
    """
    The base for all other models.
    """

    class Meta:
        database = db
        validate_backrefs = False
