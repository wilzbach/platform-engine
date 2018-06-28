# -*- coding: utf-8 -*-
from pytest import mark


def test_stories_get(patch, magic, story):
    assert story.tree is not None
    assert story.context is None
    assert story.version is None


@mark.asyncio
async def test_stories_argument_by_name_replacement(patch, magic, story):
    """
    Ensures that a replacement resolve can be performed.
    """
    assert await story.argument_by_name(
        story.line('1'), 'msg', encode=False
    ) == 'Hi, I am Asyncy!'

    assert await story.argument_by_name(
        story.line('1'), 'msg', encode=True
    ) == "'Hi, I am Asyncy!'"
