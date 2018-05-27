# -*- coding: utf-8 -*-
import asyncio
import os
import traceback
from concurrent.futures import ThreadPoolExecutor

import click

from raven.contrib.tornado import AsyncSentryClient

import tornado
from tornado import web

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


class RunStoryHandler(tornado.web.RequestHandler):

    @classmethod
    async def run_story(cls, request_response, io_loop):
        req = ujson.loads(request_response.request.body)

        logger.log('http-request-run-story', req['story_name'], req['app_id'])

        context = req.get('context', {})
        context[ContextConstants.server_request] = request_response
        context[ContextConstants.server_io_loop] = io_loop

        await Story.run(app, logger,
                        story_name=req['story_name'],
                        context=context,
                        block=req.get('block'), start=req.get('line'))

    @web.asynchronous
    async def post(self):
        io_loop = tornado.ioloop.IOLoop.current()
        try:
            await RunStoryHandler.run_story(self, io_loop)
        except Exception as e:
            logger.log_raw('error', 'Story execution failed; cause=' + str(e))
            self.set_status(500, 'Story execution failed')
            self.finish()

    def is_finished(self):
        return self._finished

    def is_not_finished(self):
        return self.is_finished() is False


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
