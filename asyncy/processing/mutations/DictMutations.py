# -*- coding: utf-8 -*-


class DictMutations:

    @classmethod
    def size(cls, mutation, value, story, line, operator):
        return len(value)

    @classmethod
    def keys(cls, mutation, value, story, line, operator):
        return list(value.keys())

    @classmethod
    def values(cls, mutation, value, story, line, operator):
        return list(value.values())

    @classmethod
    def pop(cls, mutation, value, story, line, operator):
        key = story.argument_by_name(mutation, 'key')
        return value.pop(key, None)

    @classmethod
    def flatten(cls, mutation, value, story, line, operator):
        out = []
        for k, v in value.items():
            out.append([k, v])
        return out

    @classmethod
    def get(cls, mutation, value, story, line, operator):
        key = story.argument_by_name(mutation, 'key')
        return value.get(key)

    @classmethod
    def contains(cls, mutation, value, story, line, operator):
        key = story.argument_by_name(mutation, 'key')
        return value.get(key) is not None
