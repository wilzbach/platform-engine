# -*- coding: utf-8 -*-
import requests

from evenflow.Stories import Stories


def test_stories_get(mocker):
    mocker.patch.object(requests, 'get')
    result = Stories.get('owner', 'project', 'test.story')
    api_url = 'https://api.github.com/repos/owner/project/contents/test.story'
    requests.get.assert_called_with(api_url)
