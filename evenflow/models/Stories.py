# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

from .Applications import Applications
from .Base import BaseModel
from .Repositories import Repositories


class Stories(BaseModel):
    filename = CharField()
    version = CharField()
    application = ForeignKeyField(Applications)
    repository = ForeignKeyField(Repositories)
