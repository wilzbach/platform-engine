# -*- coding: utf-8 -*-
from playhouse import db_url
from playhouse.postgres_ext import PostgresqlExtDatabase


class Database(PostgresqlExtDatabase):

    def from_url(self, database_url):
        db_dict = db_url.parse(database_url)
        super().init(db_dict['database'], host=db_dict['host'],
                     port=db_dict['port'], user=db_dict['user'],
                     password=db_dict['password'])
