# -*- coding: utf-8 -*-
from peewee import CharField

from .Base import BaseModel


class Users(BaseModel):
    name = CharField()
    email = CharField()
    github_handle = CharField()
