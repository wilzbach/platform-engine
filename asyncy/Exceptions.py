# -*- coding: utf-8 -*-


class AsyncyError(Exception):

    def __init__(self, message=None, story=None, line=None):
        self.story = story
        self.line = line
        super().__init__(message)


class ContainerSpecNotRegisteredError(AsyncyError):
    def __init__(self, container_name):
        super().__init__(message=f'Service {container_name} not registered!')


class TooManyVolumes(AsyncyError):
    def __init__(self, volume_count, max_volumes):
        super().__init__(
            message=f'Your app makes use of {volume_count} volumes. '
                    f'The total permissible limit during Asyncy Beta is '
                    f'{max_volumes} volumes. Please see '
                    f'https://docs.asyncy.com/faq/ for more information.')


class TooManyServices(AsyncyError):
    def __init__(self, service_count, max_services):
        super().__init__(
            message=f'Your app makes use of {service_count} services. '
                    f'The total permissible limit during Asyncy Beta is '
                    f'{max_services} services. Please see '
                    f'https://docs.asyncy.com/faq/ for more information.')


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


class EnvironmentVariableNotFound(AsyncyError):
    def __init__(self, service=None, variable=None, story=None, line=None):
        assert service is not None
        assert variable is not None
        super().__init__(
            f'The service "{service}" requires an environment variable '
            f'"{variable}" which was not specified. '
            f'Please set it by running '
            f'"$ asyncy config set {service}.{variable}=<value>" '
            f'in your Asyncy app directory', story, line)
