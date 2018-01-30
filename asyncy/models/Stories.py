# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

from storyscript import resolver
from storyscript.parser import Parser

from .Base import BaseModel
from .Repositories import Repositories


class Stories(BaseModel):
    filename = CharField()
    version = CharField(null=True)
    repository = ForeignKeyField(Repositories)

    def backend(self, app_identifier, pem_path, installation_id):
        self.repository.backend(app_identifier, pem_path, installation_id)

    def get_contents(self):
        return self.repository.contents(self.filename, self.version)

    def data(self, initial_data):
        self._initial_data = initial_data

    def environment(self):
        config = self.repository.config()
        if config:
            if 'env' in config:
                return config['env']
        return {}

    def build_tree(self):
        story = self.get_contents()
        self.tree = Parser().parse(story).json()

    def line(self, line_number):
        return self.tree['script'][line_number]

    def resolve(self, logger, line_number):
        args = self.line(line_number)['args']
        item = resolver.resolve_obj(self._initial_data, args)
        logger.log('story-resolve', args, item)
        return item
