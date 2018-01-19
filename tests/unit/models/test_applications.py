# -*- coding: utf-8 -*-
from evenflow.models import Applications, BaseModel

from peewee import CharField, ForeignKeyField


def test_applications():
    assert isinstance(Applications.name, CharField)
    assert isinstance(Applications.user, ForeignKeyField)
    assert isinstance(Applications.initial_data, CharField)
    assert Applications.initial_data.null is True
    assert issubclass(Applications, BaseModel)


def test_applications_get_story(application):
    story = application.get_story('test.story')
    application.stories.where.assert_called_with(True)
    assert story == application.stories.where().get()
