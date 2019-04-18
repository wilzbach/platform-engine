# -*- coding: utf-8 -*-


class DictMutations:

    @classmethod
    def length(cls, mutation, value, story, line, operator):
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
        default = story.argument_by_name(mutation, 'default')
        return value.get(key, default)

    @classmethod
    def contains(cls, mutation, value, story, line, operator):
        key = story.argument_by_name(mutation, 'key')
        if key is not None:
            return key in value
        item = story.argument_by_name(mutation, 'value')
        for v in value.values():
            if v == item:
                return True
        return False
