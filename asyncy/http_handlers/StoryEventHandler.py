# -*- coding: utf-8 -*-
import tornado
from tornado import web

import ujson

from ..Apps import Apps
from .BaseHandler import BaseHandler
from .. import Metrics
from ..constants import ContextConstants
from ..processing import Story


class StoryEventHandler(BaseHandler):

    async def run_story(self, app_id, story_name, block, event_body):
        io_loop = tornado.ioloop.IOLoop.current()
        context = {
            ContextConstants.service_event: event_body,
            ContextConstants.server_io_loop: io_loop,
            ContextConstants.server_request: self
        }

        app = Apps.get(app_id)

        await Story.run(app, self.logger,
                        story_name=story_name,
                        context=context,
                        block=block)

    @web.asynchronous
    @Metrics.story_request.time()
    async def post(self):
        self.app.sentry_client.context.clear()
        self.app.sentry_client.user_context({
            'app_uuid': self.app.app_id,
        })

        story_name = self.get_argument('story')
        block = self.get_argument('block')
        app_id = self.get_argument('app')

        try:
            event_body = ujson.loads(self.request.body)
            self.logger.info(f'Running story for {app_id}: '
                             f'{story_name} @ {block} for '
                             f'event {event_body}')
            await self.run_story(app_id, story_name, block, event_body)
            self.set_status(200)
            self.finish()
        except BaseException as e:
            self.handle_story_exc(story_name, e)
