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
    @click.option('--block', help='Processes the block after this line')
    def run(app_id, story, block):
        process_story.delay(app_id, story, block=block)
