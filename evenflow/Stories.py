# -*- coding: utf-8 -*-
import requests


class Stories:

    def get(owner, repository, story):
        api_url = 'https://api.github.com/repos/{}/{}/contents/{}'
        requests.get(api_url.format(owner, repository, story))
