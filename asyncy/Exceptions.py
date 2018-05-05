# -*- coding: utf-8 -*-
import docker


class AsyncyError(Exception):

    def __init__(self, message=None):
        super().__init__(message)


class DockerError(docker.errors.DockerException):

    def __init__(self, message=None):
        super().__init__(message)


class DockerContainerNotFoundError(DockerError):

    def __init__(self, message=None):
        super().__init__(message)
