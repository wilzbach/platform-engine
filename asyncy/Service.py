# -*- coding: utf-8 -*-
import os
from concurrent.futures import ThreadPoolExecutor

import click

from raven.contrib.tornado import AsyncSentryClient

import tornado
from tornado import gen, web

import ujson

from . import Version
from .App import App
from .Config import Config
from .Logger import Logger
from .constants.ContextConstants import ContextConstants
from .processing import Story

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

config = Config()
app = App(config)
logger = Logger(config)
logger.start()

# 20 is an arbitrary number. Feel free to increase it.
story_executor = ThreadPoolExecutor(max_workers=20)


class RunStoryHandler(tornado.web.RequestHandler):
    finished = False

    @classmethod
    def run_story(cls, request_response, io_loop):
        req = ujson.loads(request_response.request.body)

        logger.log('http-request-run-story', req['story_name'], req['app_id'])

        context = req.get('context', {})
        context[ContextConstants.server_request] = request_response
        context[ContextConstants.server_io_loop] = io_loop

        try:
            Story.run(app, logger,
                      story_name=req['story_name'],
                      context=context,
                      block=req.get('block'), start=req.get('line'))
        except Exception as e:
            logger.log_raw('error', 'Failed to execute story! error=' + str(e))

    @web.asynchronous
    def post(self):
        io_loop = tornado.ioloop.IOLoop.current()
        args = [self, io_loop]
        story_executor.submit(RunStoryHandler.run_story, *args)

    def on_finish(self):
        self.finished = True
        super().on_finish()

    def is_finished(self):
        return self.finished

    def is_not_finished(self):
        return self.finished is False


class Service:

    @click.group()
    def main():
        pass

    @staticmethod
    @main.command()
    @click.option('--port',
                  help='Set the port on which the HTTP server binds to',
                  default=os.getenv('PORT', '8084'))
    @click.option('--debug',
                  help='Sets the engine into debug mode',
                  default=False)
    @click.option('--sentry_dsn',
                  help='Sentry DNS for bug collection.',
                  default=os.getenv('SENTRY_DSN'))
    def start(port, debug, sentry_dsn):
        logger.log('service-init', Version.version)
        app = tornado.web.Application(
            [
                (r'/story/run', RunStoryHandler)
            ],
            debug=debug,
        )
        app.listen(port)
        app.sentry_client = AsyncSentryClient(sentry_dsn)

        logger.log('http-init', port)

        try:
            tornado.ioloop.IOLoop.current().start()
        except KeyboardInterrupt:
            logger.log_raw('info', 'Shutdown!')
