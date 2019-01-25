# -*- coding: utf-8 -*-


class AsyncyError(Exception):

    def __init__(self, message=None, story=None, line=None):
        self.story = story
        self.line = line
        super().__init__(message)


class ContainerSpecNotRegisteredError(AsyncyError):
    def __init__(self, container_name):
        super().__init__(message=f'Service {container_name} not registered!')


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


class K8sError(AsyncyError):

    def __init__(self, story=None, line=None, message=None):
        super().__init__(message, story=story, line=line)


class ServiceNotFound(AsyncyError):

    def __init__(self, story=None, line=None, name=None):
        assert name is not None
        super().__init__(
            f'The service "{name}" was not found in the Asyncy Hub. '
            f'Hint: 1. Check with the Asyncy team if this service has '
            f'been made public; 2. Service names are case sensitive',
            story=story, line=line)
