# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

from .Base import BaseModel
from .Users import Users


class Repositories(BaseModel):
    name = CharField()
    owner = CharField()
    user = ForeignKeyField(Users)
