# -*- coding: utf-8 -*-
from tornado.web import RequestHandler

from ..processing import Story
from ..constants import ContextConstants
from tornado import web
import ujson

from .BaseHandler import BaseHandler
from .. import Metrics


class StoryEventHandler(BaseHandler):

    async def run_story(self, story_name, block, event_body):
        context = {
            ContextConstants.service_event: event_body
        }

        await Story.run(self.app, self.logger,
                        story_name=story_name,
                        context=context,
                        block=block)

    @web.asynchronous
    @Metrics.story_request.time()  # TODO change event name
    async def post(self):
        self.app.sentry_client.context.clear()
        self.app.sentry_client.user_context({
            'id': self.app.beta_user_id,
        })

        story_name = self.get_argument('story')
        block = self.get_argument('block')

        try:
            event_body = ujson.loads(self.request.body)
            await self.run_story(story_name, block, event_body)
            self.set_status(204)
            self.finish()
        except BaseException as e:
            self.handle_story_exc(story_name, e)