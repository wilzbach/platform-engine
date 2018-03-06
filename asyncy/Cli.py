# -*- coding: utf-8 -*-
import click

from .CeleryTasks import process_story


class Cli:

    @click.group()
    def main():
        pass

    @staticmethod
    @main.command()
    @click.argument('story')
    @click.argument('app_id')
    def run(app_id, story):
        process_story.delay(app_id, story)
