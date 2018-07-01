# -*- coding: utf-8 -*-
import asyncio
import os
import traceback

import click

import prometheus_client

import tornado
from tornado import web

import ujson

from . import Metrics, Version
from .App import App
from .Config import Config
from .Exceptions import AsyncyError
from .Logger import Logger
from .Stories import Stories
from .constants.ContextConstants import ContextConstants
from .processing import Story
from .processing.internal import File, Http, Log
from .processing.internal.Services import Services

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

config = Config()
app = None
logger = Logger(config)
logger.start()


class RunStoryHandler(tornado.web.RequestHandler):

    @classmethod
    async def run_story(cls, req, request_response, io_loop):
        logger.log('http-request-run-story', req['story_name'])

        context = req.get('context', {})
        context[ContextConstants.server_request] = request_response
        context[ContextConstants.server_io_loop] = io_loop

        await Story.run(app, logger,
                        story_name=req['story_name'],
                        context=context,
                        block=req.get('block'),
                        function_name=req.get('function'))

        # If we're running in an http context, then we need to call finish
        # on Tornado's response object.
        if request_response.is_not_finished():
            io_loop.add_callback(request_response.finish)

    @web.asynchronous
    @Metrics.story_request.time()
    async def post(self):
        io_loop = tornado.ioloop.IOLoop.current()
        app.sentry_client.context.clear()
        app.sentry_client.user_context({
            'id': app.beta_user_id,
        })

        req = None
        try:
            req = ujson.loads(self.request.body)
            await RunStoryHandler.run_story(req, self, io_loop)
        except BaseException as e:
            logger.log_raw('error', 'Story execution failed; cause=' + str(e))
            traceback.print_exc()
            self.set_status(500, 'Story execution failed')
            self.finish()
            if isinstance(e, AsyncyError):
                assert isinstance(e.story, Stories)
                app.sentry_client.capture('raven.events.Exception', extra={
                    'story_name': e.story.name,
                    'story_line': e.line['ln']
                })
            else:
                if req is None:
                    app.sentry_client.capture('raven.events.Exception')
                else:
                    app.sentry_client.capture('raven.events.Exception', extra={
                        'story_name': req['story_name']
                    })

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
    @click.option('--prometheus_port',
                  help='Set the port on which metrics are exposed',
                  default=os.getenv('METRICS_PORT', '8085'))
    @click.option('--debug',
                  help='Sets the engine into debug mode',
                  default=False)
    @click.option('--sentry_dsn',
                  help='Sentry DNS for bug collection.',
                  default=os.getenv('SENTRY_DSN'))
    @click.option('--release',
                  help='The version being released (provide a Git commit ID)',
                  default=os.getenv('RELEASE_VER'))
    @click.option('--user_id',
                  help='The Asyncy User ID',
                  default=os.getenv('BETA_USER_ID'))
    def start(port, debug, sentry_dsn, release, user_id, prometheus_port):
        global app
        app = App(config, logger, beta_user_id=user_id,
                  sentry_dsn=sentry_dsn, release=release)

        Services.logger = logger

        # Init internal services.
        File.init()
        Log.init()
        Http.init()
        Services.log_registry()

        logger.log('service-init', Version.version)
        web_app = tornado.web.Application(
            [
                (r'/story/run', RunStoryHandler)
            ],
            debug=debug,
        )
        web_app.listen(port)
        prometheus_client.start_http_server(port=int(prometheus_port))

        logger.log('http-init', port)

        loop = asyncio.get_event_loop()
        loop.create_task(app.bootstrap())

        try:
            tornado.ioloop.IOLoop.current().start()
        except KeyboardInterrupt:
            logger.log_raw('info', 'Shutdown!')

        logger.log_raw('info', 'Unregistering with the gateway...')
        loop.run_until_complete(app.destroy())
