# -*- coding: utf-8 -*-
from peewee import CharField, ForeignKeyField

from .Base import BaseModel
from .Users import Users
from ..Github import Github


class Repositories(BaseModel):
    name = CharField()
    organization = CharField()
    owner = ForeignKeyField(Users)

    def backend(self, app_identifier, pem_path, installation_id):
        self.github = Github(app_identifier, pem_path)
        self.github.authenticate(installation_id)

    def contents(self, filename, version):
        return self.github.get_contents(self.organization, self.name, filename,
                                        version=version)
