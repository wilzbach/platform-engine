# -*- coding: utf-8 -*-


class AsyncyError(Exception):

    def __init__(self, message=None):
        super().__init__(message)


class GithubAuthError(AsyncyError):
    def __init__(self, github_app, installation_id):
        message = 'Cannot authenticate app {} with installation id {}'
        super().__init__(message.format(github_app, installation_id))
