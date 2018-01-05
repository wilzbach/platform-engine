# -*- coding: utf-8 -*-


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
