# -*- coding: utf-8 -*-
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

    def authenticate(self, installation_id):
        """
        Authenticate the app as an installation
        """
        token = Jwt.encode(self.github_pem, 500, iss=self.github_app)
        url = self.make_url('installations', installation_id)
        headers = {'Authorization': 'Bearer {}'.format(token),
                   'Accept': 'application/vnd.github.machine-man-preview+json'}
        response = Http.post(url, transformation='json', headers=headers)
        self.access_token = response['token']

    def get_contents(self, organization, repository, file, version=None):
        url = self.make_url('contents', organization, repository, file)
        headers = {'Authorization': 'Bearer {}'.format(self.access_token),
                   'Accept': 'application/vnd.github.machine-man-preview+json'}
        kwargs = {'params': {'ref': version}, 'headers': headers}
        return Http.get(url, transformation='base64', **kwargs)
