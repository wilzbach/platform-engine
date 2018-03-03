# -*- coding: utf-8 -*-
import click

from .Config import Config
from .models import (Applications, ApplicationsStories, Repositories, Stories,
                     Users, db)


class Cli:

    @staticmethod
    def init_db():
        config = Config()
        db.from_url(config.database)

    @click.group()
    def main():
        pass

    @main.command()
    def install():
        Cli.init_db()
        models = [Applications, ApplicationsStories, Repositories, Stories,
                  Users]
        db.create_tables(models, safe=True)

    @staticmethod
    @main.command()
    @click.argument('name')
    @click.argument('email')
    @click.argument('handle')
    @click.argument('installation')
    def add_user(name, email, handle, installation):
        Cli.init_db()
        user = Users(name=name, email=email, github_handle=handle,
                     installation_id=installation)
        user.save()
        click.echo('User created!')

    @staticmethod
    @main.command()
    @click.argument('name')
    @click.argument('username')
    def add_application(name, username):
        Cli.init_db()
        user = Users.get(Users.name == username)
        application = Applications(name=name, user=user)
        application.save()
        click.echo('Application created!')

    @staticmethod
    @main.command()
    @click.argument('name')
    @click.argument('organization')
    @click.argument('username')
    def add_repository(name, organization, username):
        Cli.init_db()
        user = Users.get(Users.name == username)
        repository = Repositories(name=name, organization=organization,
                                  owner=user)
        repository.save()
        click.echo('Repository created!')

    @staticmethod
    @main.command()
    @click.argument('filename')
    @click.argument('repository')
    def add_story(filename, repository):
        """
        Registers a story in the database
        """
        Cli.init_db()
        repo = Repositories.get(Repositories.name == repository)
        story = Stories(filename=filename, repository=repo)
        story.save()
        click.echo('Story created!')
