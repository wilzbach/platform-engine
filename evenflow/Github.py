# -*- coding: utf-8 -*-
from .Http import Http
from .Jwt import Jwt


class Github:

    api_url = 'https://api.github.com'

    def __init__(self, github_pem, user=None):
        self.github_pem = github_pem
        self.user = user

    def url(self, page):
        pages = {
            'repository': 'repos/{}/{}/contents',
            'installations': 'installations/{}/access_tokens'
        }

        if page in pages:
            base = '{}/{}'.format(self.api_url, '{}')
            return base.format(pages[page])

    def make_url(self, page, *args):
        return self.url(page).format(*args)

    def get_token(self):
        token = Jwt.encode(self.github_pem, 500, iss='issuer')
        url = self.make_url('installations', self.user.github_handle)
        headers = {'Authorization': 'Bearer {}'.format(token)}
        response = Http.post(url, transformation='json', headers=headers)
        return response['token']

    def get_contents(self, organization, repository, file, version=None):
        url = self.make_url('repository', organization, repository, file)
        headers = {'Authorization': 'Bearer {}'.format(self.get_token())}
        kwargs = {'params': {'ref': version}, 'headers': headers}
        return Http.get(url, transformation='base64', **kwargs)
