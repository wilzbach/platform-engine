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

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.parents = []

    def backend(self, logger, app_identifier, pem_path, installation_id):
        self.repository.backend(logger, app_identifier, pem_path,
                                installation_id)

    def get_contents(self):
        return self.repository.contents(self.filename, self.version)

    def set_data(self, initial_data):
        self.data = initial_data

    def environment(self):
        return self.repository.config(self.filename)

    def build_tree(self):
        story = self.get_contents()
        self.tree = Parser().parse(story).json()

    def line(self, line_number):
        return self.tree['script'][line_number]

    def resolve(self, logger, line_number):
        args = self.line(line_number)['args']
        item = Resolver.resolve(args, self.data)
        logger.log('story-resolve', args, item)
        return item

    def add_parent(self, parent):
        if parent:
            self.parents.append(parent)

    def build(self, logger, application, app_id, pem_path, parent=None):
        """
        Does everything needed to have the story ready for execution.
        """
        self.set_data(application.initial_data)
        self.backend(logger, app_id, pem_path, application.installation_id())
        self.build_tree()
        self.add_parent(parent)

    def start_line(self, line_number):
        self.results[line_number] = {'start': time.time()}

    def end_line(self, line_number, output):
        dictionary = {'output': output, 'end': time.time(),
                      'start': self.results[line_number]['start']}
        self.results[line_number] = dictionary
