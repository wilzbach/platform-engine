# -*- coding: utf-8 -*-
from peewee import CharField, IntegerField

from .Base import BaseModel


class Users(BaseModel):
    name = CharField()
    email = CharField()
    github_handle = CharField()
    installation_id = IntegerField(null=True)
