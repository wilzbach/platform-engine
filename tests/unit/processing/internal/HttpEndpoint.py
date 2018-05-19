# -*- coding: utf-8 -*-
from asyncy.processing.internal.HttpEndpoint import HttpEndpoint

import pytest
from pytest import mark


@mark.parametrize('http_object', ['request', 'response', 'foo'])
def test_http_endpoint_run(patch, story, http_object):
    line = {
        'container': http_object
    }
    patch.many(HttpEndpoint, ['access_request', 'access_response'])
    if http_object is 'request':
        HttpEndpoint.run(story, line)
        HttpEndpoint.access_request.assert_called_with(story, line)
    elif http_object is 'response':
        HttpEndpoint.run(story, line)
        HttpEndpoint.access_response.assert_called_with(story, line)
    else:
        with pytest.raises(NotImplementedError):
            HttpEndpoint.run(story, line)
