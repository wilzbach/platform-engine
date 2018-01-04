# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

import requests

import storyscript
from storyscript import resolver

from .Applications import Applications
from .Base import BaseModel
from .Repositories import Repositories


class Stories(BaseModel):
    filename = CharField()
    version = CharField(null=True)
    application = ForeignKeyField(Applications)
    repository = ForeignKeyField(Repositories)

    def get_contents(self):
        api_url = 'https://api.github.com/repos/{}/{}/contents/{}'
        file_url = api_url.format(self.repository.owner, self.repository.name,
                                  self.filename)
        requests.get(file_url, params={'ref': self.version})

    def build_tree(self):
        story = self.get_contents()
        self.tree = storyscript.parse(story).json()

    def resolve(self, line_number, data):
        args = self.tree['story'][line_number]['args']
        return resolver.resolve_obj(data, args)
