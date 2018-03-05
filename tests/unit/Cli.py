# -*- coding: utf-8 -*-
from asyncy.CeleryTasks import process_story
from asyncy.Cli import Cli
from asyncy.models import (Applications, ApplicationsStories, Repositories,
                           Stories, Users, db)

from click.testing import CliRunner

from pytest import fixture


@fixture
def runner():
    return CliRunner()


def test_cli_init_db(patch, config):
    patch.object(db, 'from_url')
    Cli.init_db()
    db.from_url.assert_called_with(config.database)


def test_cli_install(patch, runner):
    patch.object(db, 'create_tables')
    patch.object(Cli, 'init_db')
    runner.invoke(Cli.install)
    assert Cli.init_db.call_count == 1
    models = [Applications, ApplicationsStories, Repositories, Stories, Users]
    db.create_tables.assert_called_with(models, safe=True)


def test_cli_adduser(patch, runner):
    patch.object(Cli, 'init_db')
    patch.object(Users, '__init__', return_value=None)
    patch.object(Users, 'save')
    result = runner.invoke(Cli.add_user, ['test', 'email', 'handle', 'id'])
    assert Cli.init_db.call_count == 1
    args = {'name': 'test', 'email': 'email', 'github_handle': 'handle',
            'installation_id': 'id'}
    Users.__init__.assert_called_with(**args)
    assert Users.save.call_count == 1
    assert result.exit_code == 0
    assert result.output == 'User created!\n'


def test_cli_add_application(patch, user, runner):
    patch.object(Cli, 'init_db')
    patch.object(Users, 'get', return_value=user)
    patch.object(Applications, '__init__', return_value=None)
    patch.object(Applications, 'save')
    result = runner.invoke(Cli.add_application, ['name', 'username'])
    assert Cli.init_db.call_count == 1
    Users.get.assert_called_with(True)
    Applications.__init__.assert_called_with(name='name', user=user)
    assert Applications.save.call_count == 1
    assert result.exit_code == 0
    assert result.output == 'Application created!\n'


def test_cli_add_repository(patch, user, runner):
    patch.object(Cli, 'init_db')
    patch.object(Users, 'get', return_value=user)
    patch.object(Repositories, '__init__', return_value=None)
    patch.object(Repositories, 'save')
    result = runner.invoke(Cli.add_repository, ['name', 'org', 'user'])
    assert Cli.init_db.call_count == 1
    Users.get.assert_called_with(True)
    args = {'name': 'name', 'organization': 'org', 'owner': user}
    Repositories.__init__.assert_called_with(**args)
    assert Repositories.save.call_count == 1
    assert result.exit_code == 0
    assert result.output == 'Repository created!\n'


def test_cli_add_story(patch, repository, runner):
    patch.object(Cli, 'init_db')
    patch.object(Repositories, 'get', return_value=repository)
    patch.object(Stories, '__init__', return_value=None)
    patch.object(Stories, 'save')
    result = runner.invoke(Cli.add_story, ['test.story', 'org/repo'])
    assert Cli.init_db.call_count == 1
    Repositories.get.assert_called_with(True)
    args = {'filename': 'test.story', 'repository': repository}
    Stories.__init__.assert_called_with(**args)
    assert Stories.save.call_count == 1
    assert result.exit_code == 0
    assert result.output == 'Story created!\n'


def test_cli_run(patch, runner):
    patch.object(process_story, 'delay')
    result = runner.invoke(Cli.run, ['story', 'app_id'])
    process_story.delay.assert_called_with('app_id', 'story')
    assert result.exit_code == 0
