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


def test_cli_adduser(patch, config, runner):
    patch.object(db, 'from_url')
    patch.object(Users, '__init__', return_value=None)
    patch.object(Users, 'save')
    result = runner.invoke(Cli.add_user, ['test', 'email', 'handle', 'id'])
    db.from_url.assert_called_with(config.database)
    args = {'name': 'test', 'email': 'email', 'github_handle': 'handle',
            'installation_id': 'id'}
    Users.__init__.assert_called_with(**args)
    assert Users.save.call_count == 1
    assert result.exit_code == 0
    assert result.output == 'User created!\n'


def test_cli_add_application(patch, config, user, runner):
    patch.object(db, 'from_url')
    patch.object(Users, 'get', return_value=user)
    patch.object(Applications, '__init__', return_value=None)
    patch.object(Applications, 'save')
    result = runner.invoke(Cli.add_application, ['name', 'username'])
    Users.get.assert_called_with(True)
    Applications.__init__.assert_called_with(name='name', user=user)
    assert Applications.save.call_count == 1
    assert result.exit_code == 0
    assert result.output == 'Application created!\n'
