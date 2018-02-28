# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

from .Base import BaseModel
from .Users import Users
from ..Github import Github
from ..utils import Yaml


class Repositories(BaseModel):
    name = CharField()
    organization = CharField()
    owner = ForeignKeyField(Users)

    def backend(self, logger, app_identifier, pem_path, installation_id):
        self.github = Github(logger, app_identifier, pem_path)
        self.github.authenticate(installation_id)

    def contents(self, filename, version):
        return self.github.get_contents(self.organization, self.name, filename,
                                        version=version)

    def config(self):
        contents = self.github.get_contents(self.organization, self.name,
                                            'asyncy.yml')
        if contents:
            return Yaml.string(contents)
