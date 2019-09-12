# -*- coding: utf-8 -*-


def test_story_get(patch, magic, story):
    assert story.tree is not None
    assert story._context == []
    assert story.version is None


def test_story_argument_by_name_replacement(patch, magic, story):
    """
    Ensures that a replacement resolve can be performed.
    """
    assert story.argument_by_name(
        story.line('1'), 'msg', encode=False
    ) == 'Hi, I am Asyncy!'

    assert story.argument_by_name(
        story.line('1'), 'msg', encode=True
    ) == "'Hi, I am Asyncy!'"
