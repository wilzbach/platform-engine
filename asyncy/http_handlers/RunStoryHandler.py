# -*- coding: utf-8 -*-
import tornado
from tornado import ioloop, web

import ujson

from .BaseHandler import BaseHandler
from .. import Metrics
from ..constants.ContextConstants import ContextConstants
from ..processing import Story


class RunStoryHandler(BaseHandler):

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
            if req is None:
                self.handle_story_exc(None, e)
            else:
                self.handle_story_exc(req['story_name'], e)
