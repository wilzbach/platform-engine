# -*- coding: utf-8 -*-
import random


class ListMutations:

    @classmethod
    def index(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, 'of')
        try:
            return value.index(item)
        except ValueError:
            return -1

    @classmethod
    def length(cls, mutation, value, story, line, operator):
        return len(value)

    @classmethod
    def append(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, 'item')
        return value.append(item)

    @classmethod
    def prepend(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, 'item')
        return value.insert(0, item)

    @classmethod
    def random(cls, mutation, value, story, line, operator):
        return random.choice(value)

    @classmethod
    def reverse(cls, mutation, value, story, line, operator):
        value.reverse()

    @classmethod
    def sort(cls, mutation, value, story, line, operator):
        value.sort()

    @classmethod
    def min(cls, mutation, value, story, line, operator):
        return min(value)

    @classmethod
    def max(cls, mutation, value, story, line, operator):
        return max(value)

    @classmethod
    def sum(cls, mutation, value, story, line, operator):
        return sum(value)

    @classmethod
    def contains(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, 'item')
        return item in value

    @classmethod
    def unique(cls, mutation, value, story, line, operator):
        tmp_set = set()
        i = 0
        while i < len(value):
            if value[i] in tmp_set:
                del value[i]
            else:
                tmp_set.add(value[i])
                i += 1

    @classmethod
    def remove(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, 'item')
        try:
            value.remove(item)
        except ValueError:
            # The value to be removed is not in the list.
            pass

    @classmethod
    def replace(cls, mutation, value, story, line, operator):
        by = story.argument_by_name(mutation, 'by')
        item = story.argument_by_name(mutation, 'item')
        for i, el in enumerate(value):
            if el == item:
                value[i] = by
