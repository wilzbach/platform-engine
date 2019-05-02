# -*- coding: utf-8 -*-


class StringMutations:

    @classmethod
    def length(cls, mutation, value, story, line, operator):
        return len(value)

    @classmethod
    def replace(cls, mutation, value, story, line, operator):
        by = story.argument_by_name(mutation, 'by')
        item = story.argument_by_name(mutation, 'item')
        if item is not None:
            return value.replace(item, by)

        pattern = story.argument_by_name(mutation, 'pattern')
        return pattern.sub(by, value)

    @classmethod
    def contains(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, 'item')
        if item is not None:
            # string contains item:string -> boolean
            return item in value

        # string contains pattern:regexp -> boolean
        pattern = story.argument_by_name(mutation, 'pattern')
        return pattern.search(value) is not None

    @classmethod
    def split(cls, mutation, value, story, line, operator):
        by = story.argument_by_name(mutation, 'by')
        return value.split(by)

    @classmethod
    def uppercase(cls, mutation, value, story, line, operator):
        return value.upper()

    @classmethod
    def lowercase(cls, mutation, value, story, line, operator):
        return value.lower()

    @classmethod
    def capitalize(cls, mutation, value, story, line, operator):
        return value.title()

    @classmethod
    def substring(cls, mutation, value, story, line, operator):
        start = story.argument_by_name(mutation, 'start')
        if start is None:
            start = 0
        end = story.argument_by_name(mutation, 'end')
        if end is None:
            return value[start:]
        return value[start:end]

    @classmethod
    def startswith(cls, mutation, value, story, line, operator):
        prefix = story.argument_by_name(mutation, 'prefix')
        return value.startswith(prefix)

    @classmethod
    def endswith(cls, mutation, value, story, line, operator):
        suffix = story.argument_by_name(mutation, 'suffix')
        return value.endswith(suffix)

    @classmethod
    def trim(cls, mutation, value, story, line, operator):
        return value.strip()
