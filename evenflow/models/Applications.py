# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

from .Base import BaseModel
from .Users import Users


class Applications(BaseModel):

    name = CharField()
    user = ForeignKeyField(Users)
