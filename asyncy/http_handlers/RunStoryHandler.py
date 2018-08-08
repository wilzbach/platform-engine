# -*- coding: utf-8 -*-
import tornado
from tornado import web

import ujson

from .. import Metrics
from ..Exceptions import AsyncyError
from ..Stories import Stories
from ..constants.ContextConstants import ContextConstants
from ..processing import Story


class RunStoryHandler(tornado.web.RequestHandler):

    logger = None
    app = None

    def initialize(self, app, logger):
        self.app = app
        self.logger = logger

    async def run_story(self, req, request_response, io_loop):
        self.logger.log('http-request-run-story', req['story_name'])

        context = req.get('context', {})
        context[ContextConstants.server_request] = request_response
        context[ContextConstants.gateway_request] = req
        context[ContextConstants.server_io_loop] = io_loop

        await Story.run(self.app, self.logger,
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
        self.app.sentry_client.context.clear()
        self.app.sentry_client.user_context({
            'id': self.app.beta_user_id,
        })

        req = None
        try:
            req = ujson.loads(self.request.body)
            await self.run_story(req, self, io_loop)
        except BaseException as e:
            self.logger.error(f'Story execution failed; cause={str(e)}', exc=e)
            self.set_status(500, 'Story execution failed')
            self.finish()
            if isinstance(e, AsyncyError):
                assert isinstance(e.story, Stories)
                self.app.sentry_client.capture(
                    'raven.events.Exception',
                    extra={
                        'story_name': e.story.name,
                        'story_line': e.line['ln']
                    })
            else:
                if req is None:
                    self.app.sentry_client.capture('raven.events.Exception')
                else:
                    self.app.sentry_client.capture(
                        'raven.events.Exception',
                        extra={
                            'story_name': req[
                                'story_name']
                        })

    def is_finished(self):
        return self._finished

    def is_not_finished(self):
        return self.is_finished() is False
