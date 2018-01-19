# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

from storyscript import resolver
from storyscript.parser import Parser

from .Base import BaseModel
from .Repositories import Repositories
from ..Github import Github


class Stories(BaseModel):
    filename = CharField()
    version = CharField(null=True)
    repository = ForeignKeyField(Repositories)

    def provider(self, app_identifier, app_name, pem_path):
        self.github = Github(app_identifier, pem_path, app_name)

    def get_contents(self):
        args = (self.repository.owner, self.repository.name, self.filename)
        return self.github.get_contents(*args, version=self.version)

    def build_tree(self):
        story = self.get_contents()
        self.tree = Parser().parse(story).json()

    def resolve(self, line_number, data):
        args = self.tree['story'][line_number]['args']
        return resolver.resolve_obj(data, args)
