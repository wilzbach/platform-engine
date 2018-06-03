# -*- coding: utf-8 -*-


class AsyncyError(Exception):

    def __init__(self, message=None, story=None, line=None):
        self.story = story
        self.line = line
        super().__init__(message)


class ArgumentNotFoundError(AsyncyError):

    def __init__(self, story=None, line=None, name=None):
        message = None
        if name is not None:
            message = name + ' is required, but not found'

        super().__init__(message, story=story, line=line)


class InvalidCommandError(AsyncyError):

    def __init__(self, name, story=None, line=None):
        message = None
        if name is not None:
            message = name + ' is not implemented'

        super().__init__(message, story=story, line=line)


class DockerError(AsyncyError):

    def __init__(self, story=None, line=None, message=None):
        super().__init__(message, story=story, line=line)
