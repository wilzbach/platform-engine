# -*- coding: utf-8 -*-
from tornado.web import RequestHandler

from ..Exceptions import AsyncyError
from ..Sentry import Sentry
from ..Stories import Stories


class BaseHandler(RequestHandler):

    logger = None
    app = None

    # noinspection PyMethodOverriding
    def initialize(self, logger):
        self.logger = logger

    def handle_story_exc(self, story_name, e):
        self.logger.error(f'Story execution failed; cause={str(e)}', exc=e)
        self.set_status(500, 'Story execution failed')
        self.finish()
        if isinstance(e, AsyncyError):
            assert isinstance(e.story, Stories)
            Sentry.capture_exc(e, e.story, e.line)
        else:
            if story_name is None:
                Sentry.capture_exc(e)
            else:
                Sentry.capture_exc(e, extra={
                    'story_name': story_name
                })

    def is_finished(self):
        return self._finished

    def is_not_finished(self):
        return self.is_finished() is False
