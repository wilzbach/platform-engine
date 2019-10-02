# -*- coding: utf-8 -*-


class Case:
    def __init__(self, append=None, prepend=None, assertion=None):
        self.append = append
        self.prepend = prepend
        self.assertion = assertion


class Suite:
    def __init__(self, cases, preparation_lines=''):
        self.cases = cases
        self.preparation_lines = preparation_lines
