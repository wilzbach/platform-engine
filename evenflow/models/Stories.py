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

    def backend(self, app_identifier, pem_path, installation_id):
        self.github = Github(app_identifier, pem_path)
        self.github.authenticate(installation_id)

    def get_contents(self):
        args = (self.repository.owner, self.repository.name, self.filename)
        return self.github.get_contents(*args, version=self.version)

    def build_tree(self):
        story = self.get_contents()
        self.tree = Parser().parse(story).json()

    def resolve(self, line_number, data):
        args = self.tree['story'][line_number]['args']
        return resolver.resolve_obj(data, args)
