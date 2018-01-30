# -*- coding: utf-8 -*-
from base64 import b64decode

from .Http import Http
from .Jwt import Jwt


class Github:

    api_url = 'https://api.github.com'

    def __init__(self, github_app, github_pem):
        self.github_pem = github_pem
        self.github_app = github_app
        self.access_token = None

    def url(self, page):
        pages = {
            'contents': 'repos/{}/{}/contents/{}',
            'installations': 'installations/{}/access_tokens'
        }

        if page in pages:
            base = '{}/{}'.format(self.api_url, '{}')
            return base.format(pages[page])

    def make_url(self, page, *args):
        return self.url(page).format(*args)

    def decode_base64(self, string):
        return b64decode(string).decode()

    def _headers(self, token):
        return {'Authorization': 'Bearer {}'.format(token),
                'Accept': 'application/vnd.github.machine-man-preview+json'}

    def authenticate(self, installation_id):
        """
        Authenticate the app as an installation
        """
        token = Jwt.encode(self.github_pem, 500, iss=self.github_app)
        url = self.make_url('installations', installation_id)
        headers = self._headers(token)
        response = Http.post(url, json=True, headers=headers)
        self.access_token = response['token']

    def get_contents(self, organization, repository, file, version=None):
        """
        Gets the content of a file from a repository
        """
        url = self.make_url('contents', organization, repository, file)
        headers = self._headers(self.access_token)
        kwargs = {'params': {'ref': version}, 'headers': headers}
        response = Http.get(url, json=True, **kwargs)
        return self.decode_base64(response['content'])
