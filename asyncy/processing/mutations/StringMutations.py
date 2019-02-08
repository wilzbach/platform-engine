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
