# -*- coding: utf-8 -*-
from tornado.web import RequestHandler

from ..Exceptions import AsyncyError
from ..Stories import Stories


class BaseHandler(RequestHandler):

    logger = None
    app = None

    # noinspection PyMethodOverriding
    def initialize(self, app, logger):
        self.app = app
        self.logger = logger

    def handle_story_exc(self, story_name, e):
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
            if story_name is None:
                self.app.sentry_client.capture('raven.events.Exception')
            else:
                self.app.sentry_client.capture(
                    'raven.events.Exception',
                    extra={
                        'story_name': story_name
                    })

    def is_finished(self):
        return self._finished

    def is_not_finished(self):
        return self.is_finished() is False
