# -*- coding: utf-8 -*-
import random

from storyruntime.utils.TypeResolver import TypeResolver


class ListMutations:
    @classmethod
    def index(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, "of")
        try:
            return value.index(item)
        except ValueError:
            return -1

    @classmethod
    def length(cls, mutation, value, story, line, operator):
        return len(value)

    @classmethod
    def append(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, "item")
        value.append(item)
        return value

    @classmethod
    def prepend(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, "item")
        value.insert(0, item)
        return value

    @classmethod
    def random(cls, mutation, value, story, line, operator):
        return random.choice(value)

    @classmethod
    def reverse(cls, mutation, value, story, line, operator):
        value.reverse()
        return value

    @classmethod
    def sort(cls, mutation, value, story, line, operator):
        value.sort()
        return value

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
        item = story.argument_by_name(mutation, "item")
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
        return value

    @classmethod
    def remove(cls, mutation, value, story, line, operator):
        item = story.argument_by_name(mutation, "item")
        try:
            new_list = value[:]
            new_list.remove(item)
            return new_list
        except ValueError:
            # The value to be removed is not in the list.
            pass
        return value

    @classmethod
    def replace(cls, mutation, value, story, line, operator):
        by = story.argument_by_name(mutation, "by")
        item = story.argument_by_name(mutation, "item")
        for i, el in enumerate(value):
            if el == item:
                value[i] = by

        return value

    @classmethod
    def join(cls, mutation, value, story, line, operator):
        sep = story.argument_by_name(mutation, "sep")
        return sep.join(
            [
                TypeResolver.type_cast(
                    item=v, type_={"$OBJECT": "type", "type": "string"}
                )
                for v in value
            ]
        )
