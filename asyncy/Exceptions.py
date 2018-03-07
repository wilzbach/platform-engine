# -*- coding: utf-8 -*-


class AsyncyError(Exception):

    def __init__(self, message=None):
        super().__init__(message)
