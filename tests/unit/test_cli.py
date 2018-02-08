# -*- coding: utf-8 -*-
from asyncy.Cli import Cli
from asyncy.models import (Applications, ApplicationsStories, Repositories,
                           Stories, Users, db)

from click.testing import CliRunner

from pytest import fixture


@fixture
def runner():
    return CliRunner()


def test_cli_install(patch, config, runner):
    patch.object(db, 'from_url')
    patch.object(db, 'create_tables')
    runner.invoke(Cli.install)
    db.from_url.assert_called_with(config.database)
    models = [Applications, ApplicationsStories, Repositories, Stories, Users]
    db.create_tables.assert_called_with(models, safe=True)
