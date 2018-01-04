# -*- coding: utf-8 -*-
from peewee import Model, PostgresqlDatabase


db = PostgresqlDatabase('database',
                        user='postgres',
                        password='postgres',
                        host='localhost'
                        )


class BaseModel(Model):
    """
    The base for all other models.
    """

    class Meta:
        database = db
        validate_backrefs = False
