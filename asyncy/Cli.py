# -*- coding: utf-8 -*-
import click

import ujson

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
    @click.option('--start', help='Force story to start from this line')
    @click.option('--context', help='Context data to start the story with')
    @click.option('--environment', help='Specify story environment')
    def run(app_id, story, block, start, context, environment):
        if context:
            context = ujson.loads(context)
        if environment:
            environment = ujson.loads(environment)
        process_story.delay(app_id, story, block=block, start=start,
                            context=context, environment=environment)
