# -*- coding: utf-8 -*-
from peewee import ForeignKeyField

from .Applications import Applications
from .Base import BaseModel
from .Repositories import Repositories


class ApplicationsRepositories(BaseModel):
    repository = ForeignKeyField(Repositories)
    application = ForeignKeyField(Applications)
