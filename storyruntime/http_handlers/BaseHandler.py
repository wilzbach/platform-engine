# -*- coding: utf-8 -*-
from tornado.web import RequestHandler

from ..Apps import Apps
from ..Exceptions import StoryscriptError
from ..constants.Events import APP_REQUEST_ERROR
from ..reporting.Reporter import Reporter
from ..reporting.ReportingAgent import ReportingEvent


class BaseHandler(RequestHandler):

    logger = None

    # noinspection PyMethodOverriding
    def initialize(self, logger):
        self.logger = logger

    def handle_story_exc(self, app_id, story_name, e):
        # Always prefer the app logger if the app is available.
        try:
            logger = Apps.get(app_id).logger
        except BaseException:
            logger = self.logger
        logger.error(f'Story execution failed; cause={str(e)}', exc=e)
        self.set_status(500, 'Story execution failed')
        self.finish()

        if isinstance(e, StoryscriptError):
            re = ReportingEvent.from_release(
                e.story.app.release, APP_REQUEST_ERROR)
        else:
            re = ReportingEvent.from_exc(e)

        re.story_name = story_name
        Reporter.capture_evt(re)

    def is_finished(self):
        return self._finished

    def is_not_finished(self):
        return self.is_finished() is False
