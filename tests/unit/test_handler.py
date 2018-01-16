# -*- coding: utf-8 -*-
from evenflow.Config import Config
from evenflow.Handler import Handler
from evenflow.models import db

from playhouse import db_url


def test_handler_init_db(mocker):
    mocker.patch.object(db, 'init')
    mocker.patch.object(db_url, 'parse')
    mocker.patch.object(Config, 'get')
    Handler.init_db()
    Config.get.assert_called_with('database')
    db_url.parse.assert_called_with(Config.get())
    db.init.assert_called_with(db_url.parse())
