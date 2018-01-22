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
        args = (self.repository.organization, self.repository.name,
                self.filename)
        return self.github.get_contents(*args, version=self.version)

    def data(self, initial_data):
        self._initial_data = initial_data

    def build_tree(self):
        story = self.get_contents()
        self.tree = Parser().parse(story).json()

    def line(self, line_number):
        return self.tree['script'][line_number]

    def resolve(self, line_number):
        args = self.line(line_number)['args']
        return resolver.resolve_obj(self._initial_data, args)
