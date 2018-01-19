# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

from .Base import BaseModel
from .Stories import Stories
from .Users import Users


class Applications(BaseModel):

    name = CharField()
    user = ForeignKeyField(Users)
    initial_data = CharField(null=True)

    def get_story(self, story_name):
        return self.stories.where(Stories.filename == story_name).get()
