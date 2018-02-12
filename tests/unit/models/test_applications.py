# -*- coding: utf-8 -*-
from asyncy.models import Applications, BaseModel, Stories

from peewee import CharField, ForeignKeyField

from playhouse.postgres_ext import HStoreField

from pytest import mark


def test_applications():
    assert isinstance(Applications.name, CharField)
    assert isinstance(Applications.user, ForeignKeyField)
    assert isinstance(Applications.initial_data, HStoreField)
    assert Applications.initial_data.null is True
    assert issubclass(Applications, BaseModel)


def test_applications_get_story(application):
    story = application.get_story('test.story')
    application.stories.join.assert_called_with(Stories)
    application.stories.join().where.assert_called_with(True)
    assert story == application.stories.join().where().get().story


def test_applications_environment(application):
    application.initial_data = {'environment': {}}
    environment = application.environment()
    assert environment == application.initial_data['environment']


@mark.parametrize('data', [{'options': {}}, None])
def test_applications_environment_none(application, data):
    application.initial_data = data
    environment = application.environment()
    assert environment == {}


def test_applications_installation_id(application):
    application.user.installation_id = '123'
    assert application.installation_id() == application.user.installation_id
