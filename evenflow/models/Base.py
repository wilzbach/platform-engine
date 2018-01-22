# -*- coding: utf-8 -*-
from peewee import Model

from .Database import database


class BaseModel(Model):
    """
    The base for all other models.
    """

    class Meta:
        database = database
        validate_backrefs = False
