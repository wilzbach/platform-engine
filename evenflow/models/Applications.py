# -*- coding: utf-8 -*-
from peewee import CharField

from .Base import BaseModel


class Applications(BaseModel):

    name = CharField()
