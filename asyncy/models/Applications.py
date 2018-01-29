# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

from playhouse.postgres_ext import HStoreField

from .Base import BaseModel
from .Stories import Stories
from .Users import Users


class Applications(BaseModel):

    name = CharField()
    user = ForeignKeyField(Users)
    initial_data = HStoreField(null=True)

    def get_story(self, story_name):
        appstory = self.stories.join(Stories)\
                               .where(Stories.filename == story_name).get()
        return appstory.story
