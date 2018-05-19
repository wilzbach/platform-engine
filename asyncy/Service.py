# -*- coding: utf-8 -*-
import click

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

app = App()
config = Config()
logger = Logger(config)
logger.start()


class RunStoryHandler(tornado.web.RequestHandler):

    @web.asynchronous
    @gen.coroutine
    def post(self):
        req = ujson.loads(self.request.body)

        logger.log('http-request-run-story', req['story_name'], req['app_id'])

        context = req.get('context', {})

        context[ContextConstants.server_request] = self

        Story.run(app, logger,
                  story_name=req['story_name'],
                  context=context,
                  block=req.get('block'), start=req.get('line'))


class Service:

    @click.group()
    def main():
        pass

    @staticmethod
    @main.command()
    @click.option('--port',
                  help='Set the port on which the HTTP server binds to',
                  default='8084')
    @click.option('--debug',
                  help='Sets the engine into debug mode',
                  default=False)
    def start(port, debug):
        logger.log('service-init', Version.version)
        app = tornado.web.Application(
            [
                (r'/story/run', RunStoryHandler)
            ],
            debug=debug,
        )
        app.listen(port)

        logger.log('http-init', port)

        try:
            tornado.ioloop.IOLoop.current().start()
        except KeyboardInterrupt:
            logger.log_raw('info', 'Shutdown!')
