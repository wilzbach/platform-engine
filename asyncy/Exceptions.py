# -*- coding: utf-8 -*-


class AsyncyError(Exception):

    def __init__(self, message=None):
        super().__init__(message)


class ArgumentNotFoundError(AsyncyError):

    def __init__(self, name=None):
        message = None
        if name is not None:
            message = name + ' is required, but not found'

        super().__init__(message)


class InvalidCommandError(AsyncyError):

    def __init__(self, name=None):
        message = None
        if name is not None:
            message = name + ' is not implemented'

        super().__init__(message)


class DockerError(AsyncyError):

    def __init__(self, message=None):
        super().__init__(message)
