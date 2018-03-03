# -*- coding: utf-8 -*-
import click

from .Config import Config
from .models import (Applications, ApplicationsStories, Repositories, Stories,
                     Users, db)


class Cli:

    @click.group()
    def main():
        pass

    @main.command()
    def install():
        config = Config()
        db.from_url(config.database)
        models = [Applications, ApplicationsStories, Repositories, Stories,
                  Users]
        db.create_tables(models, safe=True)

    @main.command()
    @click.argument('name')
    @click.argument('email')
    @click.argument('handle')
    @click.argument('installation')
    def add_user(name, email, handle, installation):
        config = Config()
        db.from_url(config.database)
        user = Users(name=name, email=email, github_handle=handle,
                     installation_id=installation)
        user.save()
        click.echo('User created!')
