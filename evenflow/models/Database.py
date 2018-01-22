# -*- coding: utf-8 -*-
from peewee import PostgresqlDatabase


database = PostgresqlDatabase('database',
                              user='postgres',
                              password='postgres',
                              host='localhost'
                              )
