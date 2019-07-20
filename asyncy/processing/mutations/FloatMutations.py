# -*- coding: utf-8 -*-
import math


class FloatMutations:

    @classmethod
    def round(cls, mutation, value, story, line, operator):
        return round(value)

    @classmethod
    def ceil(cls, mutation, value, story, line, operator):
        return math.ceil(value)

    @classmethod
    def floor(cls, mutation, value, story, line, operator):
        return math.floor(value)

    @classmethod
    def sin(cls, mutation, value, story, line, operator):
        return math.sin(value)

    @classmethod
    def cos(cls, mutation, value, story, line, operator):
        return math.cos(value)

    @classmethod
    def tan(cls, mutation, value, story, line, operator):
        return math.tan(value)

    @classmethod
    def asin(cls, mutation, value, story, line, operator):
        return math.asin(value)

    @classmethod
    def acos(cls, mutation, value, story, line, operator):
        return math.acos(value)

    @classmethod
    def atan(cls, mutation, value, story, line, operator):
        return math.atan(value)

    @classmethod
    def log(cls, mutation, value, story, line, operator):
        return math.log(value)

    @classmethod
    def log2(cls, mutation, value, story, line, operator):
        return math.log2(value)

    @classmethod
    def log10(cls, mutation, value, story, line, operator):
        return math.log10(value)

    @classmethod
    def exp(cls, mutation, value, story, line, operator):
        return math.exp(value)

    @classmethod
    def abs(cls, mutation, value, story, line, operator):
        return abs(value)

    @classmethod
    def isNaN(cls, mutation, value, story, line, operator):
        return math.isnan(value)

    @classmethod
    def isInfinity(cls, mutation, value, story, line, operator):
        return math.isinf(value)

    @classmethod
    def approxEqual(cls, mutation, value, story, line, operator):
        cmp = story.argument_by_name(mutation, 'value')
        max_rel_diff = story.argument_by_name(mutation, 'maxRelDiff')
        max_abs_diff = story.argument_by_name(mutation, 'maxAbsDiff')
        if max_rel_diff is None and max_abs_diff is None:
            return math.isclose(value, cmp)
        elif max_rel_diff is None:
            return math.isclose(value, cmp, abs_tol=max_abs_diff)
        elif max_abs_diff is None:
            return math.isclose(value, cmp, rel_tol=max_rel_diff)
        else:
            return math.isclose(value, cmp,
                                rel_tol=max_rel_diff, abs_tol=max_abs_diff)

    @classmethod
    def sqrt(cls, mutation, value, story, line, operator):
        return math.sqrt(value)
