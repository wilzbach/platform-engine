# -*- coding: utf-8 -*-
from asyncy.models import Applications, BaseModel, Stories

from peewee import CharField, ForeignKeyField

from playhouse.postgres_ext import JSONField


def test_applications():
    assert isinstance(Applications.name, CharField)
    assert isinstance(Applications.user, ForeignKeyField)
    assert isinstance(Applications.initial_data, JSONField)
    assert Applications.initial_data.null is True
    assert issubclass(Applications, BaseModel)


def test_applications_get_story(application):
    story = application.get_story('test.story')
    application.stories.join.assert_called_with(Stories)
    application.stories.join().where.assert_called_with(True)
    assert story == application.stories.join().where().get().story
