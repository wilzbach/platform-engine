# -*- coding: utf-8 -*-
from peewee import ForeignKeyField

from .Applications import Applications
from .Base import BaseModel
from .Stories import Stories


class ApplicationsStories(BaseModel):
    """
    Applications and Stories have an M:M relationship, signifying that a
    story has been enabled for that application.
    """
    application = ForeignKeyField(Applications)
    story = ForeignKeyField(Stories)
