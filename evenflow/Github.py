# -*- coding: utf-8 -*-
import base64


import requests


class Github:

    api_url = 'https://api.github.com'

    def __init__(self, user=None):
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

    def get_contents(self, organization, repository, file):
        url = self.make_url('repository', organization, repository, file)
        response = requests.get(url, params={'ref': None})
        response.raise_for_status()
        return base64.b64decode(response.text)
