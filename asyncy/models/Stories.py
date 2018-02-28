# -*- coding: utf-8 -*-
import time

from peewee import CharField, ForeignKeyField

from storyscript.parser import Parser
from storyscript.resolver import Resolver

from .Base import BaseModel
from .Repositories import Repositories


class Stories(BaseModel):
    filename = CharField()
    version = CharField(null=True)
    repository = ForeignKeyField(Repositories)
    results = {}

    def backend(self, logger, app_identifier, pem_path, installation_id):
        self.repository.backend(logger, app_identifier, pem_path,
                                installation_id)

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
        item = Resolver.resolve(args, self._initial_data)
        logger.log('story-resolve', args, item)
        return item

    def set_parent(self, parent):
        self.parent = parent

    def build(self, application, app_identifier, pem_path, parent=None):
        """
        Does everything needed to have the story ready for execution.
        """
        self.data(application.initial_data)
        self.backend(app_identifier, pem_path, application.installation_id())
        self.build_tree()
        self.set_parent(parent)

    def start_line(self, line_number):
        self.results[line_number] = {'start': time.time()}

    def end_line(self, line_number, output):
        dictionary = {'output': output, 'end': time.time(),
                      'start': self.results[line_number]['start']}
        self.results[line_number] = dictionary
