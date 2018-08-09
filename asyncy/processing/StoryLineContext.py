# -*- coding: utf-8 -*-


class StoryLineContext:
    """
    StoryLineContext stores permanent context (in-memory)
    for a story and a line.
    This is useful especially when a story uses services with events.

    Usage:
    Set a k/v for a story: StoryLineContext.set(story, line, key, value)
    Get back the full context: StoryLineContext.get(story, line)
    """

    store = {}

    @classmethod
    def get_key(cls, story, line):
        return f'{story.name}:{line["ln"]}'

    @classmethod
    def set(cls, story, line, key, value):
        store_key = cls.get_key(story, line)
        store = cls.store.setdefault(store_key, {})
        store[key] = value

    @classmethod
    def get(cls, story, line):
        store_key = cls.get_key(story, line)
        store = cls.store.setdefault(store_key, {})
        return store
