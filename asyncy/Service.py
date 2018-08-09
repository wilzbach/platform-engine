# -*- coding: utf-8 -*-
import asyncio
import os
import socket

import click

import prometheus_client

import tornado
from tornado import web

from .http_handlers.StoryEventHandler import StoryEventHandler
from .http_handlers.RunStoryHandler import RunStoryHandler
from . import Version
from .App import App
from .Config import Config
from .Logger import Logger
from .processing.internal import File, Http, Log
from .processing.internal.Services import Services

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

config = Config()
app = None
logger = Logger(config)
logger.start()


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

        web_app = tornado.web.Application([

            (r'/story/run', RunStoryHandler,
             {'app': app, 'logger': logger}),

            (r'/story/event', StoryEventHandler,
             {'app': app, 'logger': logger})

        ], debug=debug)

        config.engine_host = socket.gethostname()
        config.engine_port = port

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
