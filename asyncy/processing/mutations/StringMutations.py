# -*- coding: utf-8 -*-


class StringMutations:

    @classmethod
    def length(cls, mutation, value, story, line, operator):
        return len(value)

    @classmethod
    def replace(cls, mutation, value, story, line, operator):
        pattern = story.argument_by_name(mutation, 'pattern')
        by = story.argument_by_name(mutation, 'by')
        return value.replace(pattern, by)

    @classmethod
    def contains(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, 'item')
        if item is not None:
            # string contains item:string -> boolean
            return item in value

        # string contains pattern:regexp -> boolean
        pattern = story.argument_by_name(mutation, 'pattern')
        return pattern in value

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
