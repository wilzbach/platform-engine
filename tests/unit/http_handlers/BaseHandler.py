# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from pytest import mark

from storyruntime.Exceptions import StoryscriptError
from storyruntime.constants import Events
from storyruntime.entities.ReportingEvent import ReportingEvent
from storyruntime.http_handlers.BaseHandler import BaseHandler
from storyruntime.reporting.Reporter import Reporter


def test_handle_init(magic, logger):
    app = magic()
    req = magic()
    handler = BaseHandler(app, req, logger=logger)
    assert handler.logger == logger


def test_finished(magic, logger):
    handler = BaseHandler(magic(), magic(), logger=logger)
    assert handler.is_finished() is False
    assert handler.is_not_finished() is True

    handler._finished = True
    assert handler.is_finished() is True
    assert handler.is_not_finished() is False


@mark.parametrize('exception', [StoryscriptError(
    story=MagicMock(), line={'ln': 1}), Exception()])
@mark.parametrize('story_name', [None, 'super_story'])
def test_handle_story_exc(patch, magic, logger, exception, story_name):
    handler = BaseHandler(magic(), magic(), logger=logger)
    patch.many(ReportingEvent, ['from_release', 'from_exc'])
    patch.object(Reporter, 'capture_evt')
    patch.many(handler, ['set_status', 'finish'])
    handler.handle_story_exc('app_id', story_name, exception)
    handler.set_status.assert_called_with(500, 'Story execution failed')
    handler.finish.assert_called()
    logger.error.assert_called()
    if isinstance(exception, StoryscriptError):
        ReportingEvent.from_release.assert_called_with(
            exception.story.app.release, Events.APP_REQUEST_ERROR)

        Reporter.capture_evt.assert_called_with(
            ReportingEvent.from_release.return_value)
    else:
        ReportingEvent.from_exc.assert_called_with(exception)
        Reporter.capture_evt.assert_called_with(
            ReportingEvent.from_exc.return_value)
