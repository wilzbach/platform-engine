# -*- coding: utf-8 -*-
from asyncy.models.Database import Database

from playhouse import db_url
from playhouse.postgres_ext import PostgresqlExtDatabase

from pytest import fixture


@fixture
def database():
    return Database(None)


def test_database():
    assert issubclass(Database, PostgresqlExtDatabase)


def test_database_from_url(mocker, database):
    db_dict = {'database': 'db', 'host': 'host', 'port': 'port',
               'user': 'user', 'password': 'password'}
    mocker.patch.object(PostgresqlExtDatabase, 'init')
    mocker.patch.object(db_url, 'parse', return_value=db_dict)
    database.from_url('dburl')
    db_url.parse.assert_called_with('dburl')
    PostgresqlExtDatabase.init.assert_called_with('db', host='host',
                                                  port='port', user='user',
                                                  password='password',
                                                  register_hstore=True)
