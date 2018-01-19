# -*- coding: utf-8 -*-
from peewee import CharField

from .Base import BaseModel


class Repositories(BaseModel):
    name = CharField()
    organization = CharField()
