# -*- coding: utf-8 -*-
from click.testing import CliRunner

from asyncy.Cli import Cli
from asyncy.Config import Config
from asyncy.models import (Applications, ApplicationsStories, Repositories,
                             Stories, Users, db)

from pytest import fixture


@fixture
def runner():
    return CliRunner()


def test_cli_install(mocker, runner):
    mocker.patch.object(Config, 'get')
    mocker.patch.object(db, 'from_url')
    mocker.patch.object(db, 'create_tables')
    runner.invoke(Cli.install)
    Config.get.assert_called_with('database')
    db.from_url.assert_called_with(Config.get())
    models = [Applications, ApplicationsStories, Repositories, Stories, Users]
    db.create_tables.assert_called_with(models, safe=True)
