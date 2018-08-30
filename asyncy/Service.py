# -*- coding: utf-8 -*-
import asyncio
import os
import signal
import socket

import click

import prometheus_client

import tornado
from tornado import web

from . import Version
from .App import App
from .Config import Config
from .Logger import Logger
from .http_handlers.StoryEventHandler import StoryEventHandler
from .processing.Services import Services
from .processing.internal import File, Http, Log

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

config = Config()
app = None
server = None
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
        global app, server
        app = App(config, logger, beta_user_id=user_id,
                  sentry_dsn=sentry_dsn, release=release)

        Services.logger = logger

        # Init internal services.
        File.init()
        Log.init()
        Http.init()
        Services.log_internal()

        logger.log('service-init', Version.version)
        signal.signal(signal.SIGTERM, Service.sig_handler)
        signal.signal(signal.SIGINT, Service.sig_handler)

        web_app = tornado.web.Application([
            (r'/story/event', StoryEventHandler,
             {'app': app, 'logger': logger})
        ], debug=debug)

        config.engine_host = socket.gethostname()
        config.engine_port = port

        server = tornado.httpserver.HTTPServer(web_app)
        server.listen(port)

        prometheus_client.start_http_server(port=int(prometheus_port))

        logger.log('http-init', port)

        loop = asyncio.get_event_loop()
        loop.create_task(app.bootstrap())

        tornado.ioloop.IOLoop.current().start()

        logger.log_raw('info', 'Shutdown complete!')

    @staticmethod
    def sig_handler(*args, **kwargs):
        logger.log_raw('info', f'Signal {args[0]} received.')
        tornado.ioloop.IOLoop.instance().add_callback(Service.shutdown)

    @classmethod
    async def shutdown_app(cls):
        logger.log_raw('info', 'Unregistering with the gateway...')
        await app.destroy()

        io_loop = tornado.ioloop.IOLoop.instance()
        io_loop.stop()
        loop = asyncio.get_event_loop()
        loop.stop()

    @classmethod
    def shutdown(cls):
        logger.log_raw('info', 'Shutting down...')

        server.stop()
        loop = asyncio.get_event_loop()
        loop.create_task(cls.shutdown_app())
