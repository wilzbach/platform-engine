# -*- coding: utf-8 -*-
from asyncy.Apps import Apps
from asyncy.Exceptions import ServiceNotFound
from asyncy.Logger import Logger
import pytest
from pytest import mark


def test_stories_get(patch, magic, story):
    assert story.tree is not None
    assert story.context is None
    assert story.version is None

@mark.asyncio
async def test_invalid_story_deploy(patch, config, raw_stories, logger, services):
    """
    Ensures that a story with an unknown service fails to deploy.
    """
    patch.many(Apps, ['update_release_state']) # TODO this wont work will it
    # patch.object(Apps, 'make_logger_for_app', return_value=logger)
    patch.object(Logger, 'log')

    with pytest.raises(ServiceNotFound) as snsf:
        await Apps.deploy_release(config, 'app_id', 'app_dns', 'app_version', {},
                                  raw_stories, False, False, 'owner_uuid')

@mark.asyncio
async def test_invalid_story_deploy(patch, config, raw_stories, logger, services):
    """
    Ensures that a story with an unknown service fails to deploy.
    """
    patch.many(Apps, ['update_release_state']) # TODO this wont work will it
    # patch.object(Apps, 'make_logger_for_app', return_value=logger)
    patch.object(Logger, 'log')

    with pytest.raises(ServiceNotFound) as snsf:
        await Apps.deploy_release(config, 'app_id', 'app_dns', 'app_version', {},
                                  raw_stories, False, False, 'owner_uuid')



def test_stories_argument_by_name_replacement(patch, magic, story):
    """
    Ensures that a replacement resolve can be performed.
    """
    assert story.argument_by_name(
        story.line('1'), 'msg', encode=False
    ) == 'Hi, I am Asyncy!'

    assert story.argument_by_name(
        story.line('1'), 'msg', encode=True
    ) == "'Hi, I am Asyncy!'"
