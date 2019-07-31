# -*- coding: utf-8 -*-
import typing

from storyruntime.entities.Release import Release


class ReportingEvent:
    story_name: typing.Union[str, None]
    story_line: typing.Union[str, None]
    app_name: typing.Union[str, None]
    app_uuid: typing.Union[str, None]
    app_version: typing.Union[str, None]
    owner_email: typing.Union[str, None]
    owner_uuid: typing.Union[str, None]
    event_name: typing.Union[str, None]
    exc_info: typing.Union[BaseException, None]

    def __init__(self, story_name=None, story_line=None, app_name=None,
                 app_uuid=None, app_version=None, owner_email=None,
                 event_name=None, exc_info=None, owner_uuid=None):
        self.story_name = story_name
        self.app_uuid = app_uuid
        self.app_name = app_name
        self.story_line = story_line
        self.event_name = event_name
        self.exc_info = exc_info
        self.app_version = app_version
        self.owner_email = owner_email
        self.owner_uuid = owner_uuid

    @staticmethod
    def from_release(release: Release, evt_name, exc_info=None):
        return ReportingEvent(
            app_name=release.app_name,
            app_uuid=release.app_uuid,
            app_version=release.version,
            owner_email=release.owner_email,
            owner_uuid=release.owner_uuid,
            event_name=evt_name,
            exc_info=exc_info
        )

    @staticmethod
    def from_exc(exc):
        return ReportingEvent(exc_info=exc)
