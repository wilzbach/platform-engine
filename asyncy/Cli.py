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
